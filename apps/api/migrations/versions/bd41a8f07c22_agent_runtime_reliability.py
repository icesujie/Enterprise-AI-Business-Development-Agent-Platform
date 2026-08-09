"""Add reliable Agent Run tracking and retry metadata.

Revision ID: bd41a8f07c22
Revises: c84d16e90f31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bd41a8f07c22"
down_revision: str | None = "c84d16e90f31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("correlation_id", sa.String(length=100)))
    op.add_column(
        "agent_runs",
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "agent_runs",
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
    )
    op.add_column("agent_runs", sa.Column("next_retry_at", sa.DateTime(timezone=True)))
    op.add_column("agent_runs", sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "agent_runs_attempt_count_check",
        "agent_runs",
        "attempt_count >= 0 AND attempt_count <= max_attempts",
    )
    op.create_check_constraint(
        "agent_runs_max_attempts_check",
        "agent_runs",
        "max_attempts BETWEEN 1 AND 5",
    )
    op.create_index(
        "ix_agent_runs_tenant_retry",
        "agent_runs",
        ["tenant_id", "status", "next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_runs_tenant_retry", table_name="agent_runs")
    op.drop_constraint("agent_runs_max_attempts_check", "agent_runs", type_="check")
    op.drop_constraint("agent_runs_attempt_count_check", "agent_runs", type_="check")
    op.drop_column("agent_runs", "last_heartbeat_at")
    op.drop_column("agent_runs", "next_retry_at")
    op.drop_column("agent_runs", "max_attempts")
    op.drop_column("agent_runs", "attempt_count")
    op.drop_column("agent_runs", "correlation_id")
