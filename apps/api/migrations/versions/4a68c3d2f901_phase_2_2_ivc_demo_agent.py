# ruff: noqa: E501 -- migration SQL contains stable registry references.

"""Activate the Phase 2.2 IVC demo qualification workflow.

Revision ID: 4a68c3d2f901
Revises: e27d4b90a1c5
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "4a68c3d2f901"
down_revision: str | None = "e27d4b90a1c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_ID = "10000000-0000-4000-8000-000000000001"
IVC_DOMAIN_ID = "60000000-0000-4000-8000-000000000002"
IVC_AGENT_ID = "61000000-0000-4000-8000-000000000002"
IVC_CONFIG_ID = "50000000-0000-4000-8000-000000000002"
IVC_ACTIVATION_ID = "63000000-0000-4000-8000-000000000002"
KNOWLEDGE_CAPABILITY_ID = "62000000-0000-4000-8000-000000000005"


def upgrade() -> None:
    op.create_table(
        "ivc_qualification_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_runs.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("response_locale", sa.String(20), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("qualification_level", sa.String(1), nullable=False),
        sa.Column("business_summary", sa.Text(), nullable=False),
        sa.Column("key_qualification_factors", postgresql.JSONB(), nullable=False),
        sa.Column("recommended_next_actions", postgresql.JSONB(), nullable=False),
        sa.Column("missing_information", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("risk_flags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("expert_review_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("review_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "score BETWEEN 0 AND 100",
            name="ivc_qualification_assessments_score_check",
        ),
        sa.CheckConstraint(
            "qualification_level IN ('A','B','C')",
            name="ivc_qualification_assessments_level_check",
        ),
        sa.CheckConstraint(
            "response_locale IN ('en','zh-CN','id')",
            name="ivc_qualification_assessments_locale_check",
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ivc_qualification_assessments_confidence_check",
        ),
        sa.CheckConstraint(
            "review_status IN ('pending','approved','rejected')",
            name="ivc_qualification_assessments_review_status_check",
        ),
    )
    op.create_index(
        "ix_ivc_assessments_tenant_review_created",
        "ivc_qualification_assessments",
        ["tenant_id", "review_status", "created_at"],
    )
    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    op.execute("ALTER TABLE ivc_qualification_assessments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ivc_qualification_assessments FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON ivc_qualification_assessments "
        f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
    )

    _execute_statements(
        f"""
            UPDATE domain_packages SET status = 'available' WHERE id = '{IVC_DOMAIN_ID}';
            UPDATE agents SET status = 'available' WHERE id = '{IVC_AGENT_ID}';
            UPDATE agent_configurations SET
                status = 'active',
                instructions_ref = 'sari_api.adapters.ivc_qualification_provider:IVC_QUALIFICATION_INSTRUCTIONS',
                config_digest = repeat('c', 64),
                runtime_config = jsonb_build_object(
                    'knowledge_enabled', false,
                    'execution_enabled', true,
                    'human_review_required', true
                )
            WHERE id = '{IVC_CONFIG_ID}';
            UPDATE agent_capability_bindings SET requirement_level = 'optional'
            WHERE agent_configuration_id = '{IVC_CONFIG_ID}'
              AND capability_id = '{KNOWLEDGE_CAPABILITY_ID}';
            INSERT INTO tenant_agent_activations
                (id, tenant_id, agent_id, agent_configuration_id, environment, status,
                 locale_policy, rollout_percentage, activated_at, reason)
            VALUES
                ('{IVC_ACTIVATION_ID}', '{TENANT_ID}', '{IVC_AGENT_ID}', '{IVC_CONFIG_ID}',
                 'development', 'active',
                 jsonb_build_object(
                    'default', 'en',
                    'supported', jsonb_build_array('en', 'zh-CN', 'id')
                 ), 100, now(),
                 'Phase 2.2 synthetic demo activation without knowledge retrieval or external action');
            """
    )


def downgrade() -> None:
    _execute_statements(
        f"""
            DELETE FROM tenant_agent_activations WHERE id = '{IVC_ACTIVATION_ID}';
            UPDATE agent_capability_bindings SET requirement_level = 'required'
            WHERE agent_configuration_id = '{IVC_CONFIG_ID}'
              AND capability_id = '{KNOWLEDGE_CAPABILITY_ID}';
            UPDATE agent_configurations SET
                status = 'draft',
                instructions_ref = 'sari_api.domain.packages.laboratory_animal_facility:LABORATORY_ANIMAL_FACILITY_PACKAGE',
                config_digest = repeat('b', 64),
                runtime_config = jsonb_build_object(
                    'knowledge_enabled', false,
                    'execution_enabled', false
                )
            WHERE id = '{IVC_CONFIG_ID}';
            UPDATE agents SET status = 'draft' WHERE id = '{IVC_AGENT_ID}';
            UPDATE domain_packages SET status = 'draft' WHERE id = '{IVC_DOMAIN_ID}';
            """
    )
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON ivc_qualification_assessments")
    op.drop_index(
        "ix_ivc_assessments_tenant_review_created",
        table_name="ivc_qualification_assessments",
    )
    op.drop_table("ivc_qualification_assessments")


def _execute_statements(sql: str) -> None:
    connection = op.get_bind()
    for statement in sql.split(";"):
        if statement.strip():
            connection.exec_driver_sql(statement)
