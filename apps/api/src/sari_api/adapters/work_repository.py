from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import Activity, Lead, Task, TenantMembership


class WorkNotFoundError(Exception):
    pass


class WorkVersionConflictError(Exception):
    pass


class InvalidTaskTransitionError(Exception):
    pass


TASK_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"in_progress", "completed", "cancelled"}),
    "in_progress": frozenset({"open", "completed", "cancelled"}),
    "completed": frozenset({"open"}),
    "cancelled": frozenset({"open"}),
}


class SqlAlchemyWorkRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def require_lead(self, lead_id: UUID) -> Lead:
        lead = await self._session.scalar(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.tenant_id == self._tenant_id,
                Lead.deleted_at.is_(None),
            )
        )
        if lead is None:
            raise WorkNotFoundError
        return lead

    async def require_assignee(self, membership_id: UUID) -> TenantMembership:
        membership = await self._session.scalar(
            select(TenantMembership).where(
                TenantMembership.id == membership_id,
                TenantMembership.tenant_id == self._tenant_id,
                TenantMembership.status == "active",
            )
        )
        if membership is None:
            raise WorkNotFoundError
        return membership

    async def list_tasks(
        self,
        *,
        lead_id: UUID | None = None,
        status: str | None = None,
        assigned_to: UUID | None = None,
        limit: int = 100,
    ) -> list[Task]:
        statement = select(Task).where(
            Task.tenant_id == self._tenant_id,
            Task.deleted_at.is_(None),
        )
        if lead_id is not None:
            statement = statement.where(Task.lead_id == lead_id)
        if status is not None:
            statement = statement.where(Task.status == status)
        if assigned_to is not None:
            statement = statement.where(Task.assigned_to == assigned_to)
        statement = statement.order_by(
            Task.completed_at.is_not(None),
            Task.due_at.asc().nulls_last(),
        ).limit(limit)
        result = await self._session.scalars(statement)
        return list(result.all())

    async def add_task(self, task: Task) -> Task:
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def get_task(self, task_id: UUID, *, for_update: bool = False) -> Task:
        statement = select(Task).where(
            Task.id == task_id,
            Task.tenant_id == self._tenant_id,
            Task.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        task = await self._session.scalar(statement)
        if task is None:
            raise WorkNotFoundError
        return task

    def update_task(
        self,
        task: Task,
        expected_version: int,
        changes: dict[str, Any],
    ) -> None:
        if task.version != expected_version:
            raise WorkVersionConflictError
        new_status = changes.get("status")
        if new_status is not None and new_status != task.status:
            if new_status not in TASK_TRANSITIONS[task.status]:
                raise InvalidTaskTransitionError
            changes["completed_at"] = datetime.now(UTC) if new_status == "completed" else None
        for field, value in changes.items():
            setattr(task, field, value)
        task.version += 1

    async def list_activities(self, lead_id: UUID, limit: int = 100) -> list[Activity]:
        await self.require_lead(lead_id)
        result = await self._session.scalars(
            select(Activity)
            .where(Activity.tenant_id == self._tenant_id, Activity.lead_id == lead_id)
            .order_by(Activity.occurred_at.desc(), Activity.created_at.desc())
            .limit(limit)
        )
        return list(result.all())

    async def add_activity(
        self,
        *,
        lead_id: UUID,
        activity_type: str,
        subject: str,
        actor_membership_id: UUID,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> Activity:
        await self.require_lead(lead_id)
        activity = Activity(
            tenant_id=self._tenant_id,
            lead_id=lead_id,
            activity_type=activity_type,
            occurred_at=occurred_at or datetime.now(UTC),
            subject=subject,
            description=description,
            actor_membership_id=actor_membership_id,
            metadata_json=metadata or {},
        )
        self._session.add(activity)
        await self._session.flush()
        await self._session.refresh(activity)
        return activity
