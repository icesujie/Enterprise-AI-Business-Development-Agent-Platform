"""M4 work tracking and AI qualification.

Revision ID: 5d72a9b889f1
Revises: 470b25de338d
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5d72a9b889f1"
down_revision: str | None = "470b25de338d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lead_assessments",
        sa.Column(
            "qualification",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "lead_assessments_tier_check",
        "lead_assessments",
        "tier IN ('hot','warm','cold')",
    )
    op.create_check_constraint(
        "tasks_completion_check",
        "tasks",
        "(status = 'completed' AND completed_at IS NOT NULL) OR "
        "(status <> 'completed' AND completed_at IS NULL)",
    )
    op.create_index(
        "ix_activities_tenant_lead_occurred",
        "activities",
        ["tenant_id", "lead_id", "occurred_at"],
    )

    op.execute(
        sa.text(
            """
            INSERT INTO agent_configurations (
                id, tenant_id, agent_key, version_number, status,
                instructions_ref, output_schema_version, runtime_config
            ) VALUES (
                '50000000-0000-4000-8000-000000000001',
                '10000000-0000-4000-8000-000000000001',
                'lead_qualification', 1, 'active',
                'sari_api.adapters.qualification_provider:QUALIFICATION_INSTRUCTIONS',
                'lead_qualification_output_v1',
                jsonb_build_object(
                    'rubric_key', 'commercial_kitchen_project_v1',
                    'need_weight', 35,
                    'timeline_weight', 25,
                    'budget_weight', 20,
                    'authority_weight', 20
                )
            )
            ON CONFLICT (tenant_id, agent_key, version_number)
            DO UPDATE SET status = 'active'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE agent_configurations SET status = 'draft' "
            "WHERE id = '50000000-0000-4000-8000-000000000001'"
        )
    )
    op.drop_index("ix_activities_tenant_lead_occurred", table_name="activities")
    op.drop_constraint("tasks_completion_check", "tasks", type_="check")
    op.drop_constraint("lead_assessments_tier_check", "lead_assessments", type_="check")
    op.drop_column("lead_assessments", "qualification")
