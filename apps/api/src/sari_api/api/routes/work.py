from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.models import Activity, Task
from sari_api.adapters.work_repository import (
    InvalidTaskTransitionError,
    SqlAlchemyWorkRepository,
    WorkNotFoundError,
    WorkVersionConflictError,
)
from sari_api.api.dependencies import require_permission
from sari_api.api.routes.crm import parse_if_match
from sari_api.domain.identity import Principal

router = APIRouter(prefix="/api/v1", tags=["work"])

TaskStatus = Literal["open", "in_progress", "completed", "cancelled"]
Priority = Literal["low", "normal", "high", "urgent"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TaskInput(StrictModel):
    title: str = Field(min_length=1, max_length=250)
    description: str | None = Field(default=None, max_length=5000)
    priority: Priority = "normal"
    assigned_to: UUID | None = None
    due_at: datetime | None = None


class TaskPatch(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    assigned_to: UUID | None = None
    due_at: datetime | None = None


class TaskResponse(StrictModel):
    id: UUID
    lead_id: UUID | None
    title: str
    description: str | None
    status: str
    priority: str
    assigned_to: UUID
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int


class ActivityInput(StrictModel):
    subject: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=10000)
    occurred_at: datetime | None = None


class ActivityResponse(StrictModel):
    id: UUID
    lead_id: UUID | None
    activity_type: str
    occurred_at: datetime
    subject: str
    description: str | None
    actor_membership_id: UUID
    metadata: dict[str, Any]
    created_at: datetime


async def repository(session: AsyncSession, principal: Principal) -> SqlAlchemyWorkRepository:
    repo = SqlAlchemyWorkRepository(session, principal.tenant_id)
    await repo.set_tenant_context()
    return repo


def task_response(task: Task) -> TaskResponse:
    return TaskResponse(**{field: getattr(task, field) for field in TaskResponse.model_fields})


def activity_response(activity: Activity) -> ActivityResponse:
    return ActivityResponse(
        **{
            field: getattr(activity, field)
            for field in ActivityResponse.model_fields
            if field != "metadata"
        },
        metadata=activity.metadata_json,
    )


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Work record not found.")


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    principal: Annotated[Principal, Depends(require_permission("tasks:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    lead_id: UUID | None = None,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    assigned_to: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[TaskResponse]:
    repo = await repository(session, principal)
    items = await repo.list_tasks(
        lead_id=lead_id,
        status=task_status,
        assigned_to=assigned_to,
        limit=limit,
    )
    return [task_response(item) for item in items]


@router.post("/leads/{lead_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    lead_id: UUID,
    payload: TaskInput,
    principal: Annotated[Principal, Depends(require_permission("tasks:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskResponse:
    repo = await repository(session, principal)
    try:
        lead = await repo.require_lead(lead_id)
        assignee = payload.assigned_to or principal.membership_id
        await repo.require_assignee(assignee)
        task = await repo.add_task(
            Task(
                tenant_id=principal.tenant_id,
                lead_id=lead_id,
                organization_id=lead.organization_id,
                title=payload.title,
                description=payload.description,
                priority=payload.priority,
                assigned_to=assignee,
                due_at=payload.due_at,
            )
        )
        due_at = task.due_at.isoformat() if task.due_at else None
        await repo.add_activity(
            lead_id=lead_id,
            activity_type="task_created",
            subject=f"Task created: {task.title}",
            actor_membership_id=principal.membership_id,
            metadata={"task_id": str(task.id), "due_at": due_at},
        )
        await session.commit()
        return task_response(task)
    except WorkNotFoundError as exc:
        raise not_found() from exc


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskPatch,
    principal: Annotated[Principal, Depends(require_permission("tasks:manage"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    if_match: Annotated[str, Header(alias="If-Match")],
) -> TaskResponse:
    repo = await repository(session, principal)
    try:
        task = await repo.get_task(task_id, for_update=True)
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("assigned_to"):
            await repo.require_assignee(changes["assigned_to"])
        old_status = task.status
        repo.update_task(task, parse_if_match(if_match), changes)
        if task.lead_id:
            await repo.add_activity(
                lead_id=task.lead_id,
                activity_type="task_updated",
                subject=f"Task updated: {task.title}",
                actor_membership_id=principal.membership_id,
                metadata={
                    "task_id": str(task.id),
                    "from_status": old_status,
                    "to_status": task.status,
                },
            )
        await session.commit()
        await session.refresh(task)
        return task_response(task)
    except WorkNotFoundError as exc:
        raise not_found() from exc
    except WorkVersionConflictError as exc:
        raise HTTPException(status_code=409, detail="The task changed; reload and retry.") from exc
    except InvalidTaskTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail="This task status transition is not allowed.",
        ) from exc


@router.get("/leads/{lead_id}/activities", response_model=list[ActivityResponse])
async def list_activities(
    lead_id: UUID,
    principal: Annotated[Principal, Depends(require_permission("crm:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=100, ge=1, le=200),
) -> list[ActivityResponse]:
    repo = await repository(session, principal)
    try:
        return [activity_response(item) for item in await repo.list_activities(lead_id, limit)]
    except WorkNotFoundError as exc:
        raise not_found() from exc


@router.post("/leads/{lead_id}/activities", response_model=ActivityResponse, status_code=201)
async def create_note(
    lead_id: UUID,
    payload: ActivityInput,
    principal: Annotated[Principal, Depends(require_permission("crm:write"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ActivityResponse:
    repo = await repository(session, principal)
    try:
        activity = await repo.add_activity(
            lead_id=lead_id,
            activity_type="manual_note",
            subject=payload.subject,
            description=payload.description,
            occurred_at=payload.occurred_at,
            actor_membership_id=principal.membership_id,
        )
        await session.commit()
        return activity_response(activity)
    except WorkNotFoundError as exc:
        raise not_found() from exc
