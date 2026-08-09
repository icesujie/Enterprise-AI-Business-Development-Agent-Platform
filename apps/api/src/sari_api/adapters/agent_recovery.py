from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.models import AgentRun, Tenant

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecoveredAgentRun:
    run_id: UUID
    tenant_id: UUID
    correlation_id: str | None


class AgentRunRecoveryService:
    """Recover durable Agent Runs whose transient Redis delivery was lost."""

    def __init__(self, stale_after_seconds: int) -> None:
        self._stale_after = timedelta(seconds=stale_after_seconds)

    async def recover(self) -> list[RecoveredAgentRun]:
        now = datetime.now(UTC)
        cutoff = now - self._stale_after
        recovered: list[RecoveredAgentRun] = []

        async with session_factory() as session:
            tenant_ids = list(
                (
                    await session.scalars(
                        select(Tenant.id).where(Tenant.status == "active").order_by(Tenant.id)
                    )
                ).all()
            )

        for tenant_id in tenant_ids:
            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(tenant_id)},
                )
                candidates = list(
                    (
                        await session.scalars(
                            select(AgentRun)
                            .where(
                                AgentRun.tenant_id == tenant_id,
                                or_(
                                    (
                                        (AgentRun.status == "running")
                                        & (
                                            func.coalesce(
                                                AgentRun.last_heartbeat_at,
                                                AgentRun.started_at,
                                                AgentRun.created_at,
                                            )
                                            < cutoff
                                        )
                                    ),
                                    (
                                        (AgentRun.status == "queued")
                                        & (
                                            func.coalesce(
                                                AgentRun.last_heartbeat_at,
                                                AgentRun.created_at,
                                            )
                                            < cutoff
                                        )
                                        & or_(
                                            AgentRun.next_retry_at.is_(None),
                                            AgentRun.next_retry_at <= now,
                                        )
                                    ),
                                ),
                            )
                            .with_for_update(skip_locked=True)
                            .limit(100)
                        )
                    ).all()
                )
                for run in candidates:
                    if run.status == "running" and run.attempt_count >= run.max_attempts:
                        run.status = "failed"
                        run.completed_at = now
                        run.next_retry_at = None
                        run.last_heartbeat_at = now
                        run.error_code = "worker_interrupted"
                        run.error_message_safe = (
                            "The Agent Run stopped before completion and exhausted its retry limit."
                        )
                        run.version += 1
                        logger.error(
                            "Stale Agent Run failed during recovery",
                            extra={
                                "event": "agent.run.recovery_failed",
                                "agent_run_id": str(run.id),
                                "tenant_id": str(tenant_id),
                                "attempt_count": run.attempt_count,
                                "max_attempts": run.max_attempts,
                            },
                        )
                        continue

                    if run.status == "running":
                        run.status = "queued"
                        run.error_code = "worker_interrupted"
                        run.error_message_safe = (
                            "The previous attempt stopped unexpectedly. Recovery retry queued."
                        )
                    run.next_retry_at = None
                    run.last_heartbeat_at = now
                    run.completed_at = None
                    run.version += 1
                    recovered.append(
                        RecoveredAgentRun(run.id, tenant_id, run.correlation_id)
                    )
                await session.commit()

        return recovered
