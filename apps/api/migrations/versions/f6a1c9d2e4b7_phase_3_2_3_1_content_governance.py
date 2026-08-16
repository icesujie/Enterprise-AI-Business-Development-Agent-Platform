"""Add governed marketing content persistence and RLS.

Revision ID: f6a1c9d2e4b7
Revises: d3e5f7a9b2c4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a1c9d2e4b7"
down_revision: str | None = "d3e5f7a9b2c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONTENT_TYPES = (
    "'website_article','case_study','tiktok_script','instagram_reel_script',"
    "'facebook_post','email_draft'"
)
AUDIENCES = (
    "'schools','hospitals','factories','central_kitchens','project_owners',"
    "'facility_managers'"
)
CHANNELS = "'website','tiktok','instagram','facebook','email'"


def uuid_column(name: str, target: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable,
    )


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def upgrade() -> None:
    op.create_table(
        "content_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("domain_id", "domain_packages.id"),
        uuid_column("agent_id", "agents.id", nullable=True),
        uuid_column("requested_by", "tenant_memberships.id"),
        sa.Column("content_type", sa.String(40), nullable=False),
        sa.Column("audience", sa.String(40), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("business_objective", sa.Text(), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("call_to_action", sa.Text(), nullable=False),
        sa.Column("campaign_name", sa.String(200)),
        sa.Column(
            "constraints",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "knowledge_collection_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("result_asset_id", postgresql.UUID(as_uuid=True)),
        *timestamps(),
        sa.CheckConstraint(
            f"content_type IN ({CONTENT_TYPES})", name="content_requests_type_check"
        ),
        sa.CheckConstraint(f"audience IN ({AUDIENCES})", name="content_requests_audience_check"),
        sa.CheckConstraint("language IN ('en','zh-CN')", name="content_requests_language_check"),
        sa.CheckConstraint(f"channel IN ({CHANNELS})", name="content_requests_channel_check"),
        sa.CheckConstraint(
            "status IN ('draft','queued','running','completed','insufficient_evidence',"
            "'failed','cancelled','archived')",
            name="content_requests_status_check",
        ),
    )
    op.create_index(
        "ix_content_requests_tenant_status",
        "content_requests",
        ["tenant_id", "status", "created_at"],
    )

    op.create_table(
        "content_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("domain_id", "domain_packages.id"),
        uuid_column("agent_id", "agents.id", nullable=True),
        uuid_column("request_id", "content_requests.id", nullable=True),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("content_type", sa.String(40), nullable=False),
        sa.Column("audience", sa.String(40), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        uuid_column("owner_membership_id", "tenant_memberships.id"),
        uuid_column("creator_membership_id", "tenant_memberships.id"),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        *timestamps(),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        uuid_column("archived_by", "tenant_memberships.id", nullable=True),
        sa.Column("archive_reason", sa.Text()),
        sa.CheckConstraint(f"content_type IN ({CONTENT_TYPES})", name="content_assets_type_check"),
        sa.CheckConstraint(f"audience IN ({AUDIENCES})", name="content_assets_audience_check"),
        sa.CheckConstraint("language IN ('en','zh-CN')", name="content_assets_language_check"),
        sa.CheckConstraint(f"channel IN ({CHANNELS})", name="content_assets_channel_check"),
        sa.CheckConstraint(
            "status IN ('draft','generated','review','approved','archived')",
            name="content_assets_status_check",
        ),
        sa.CheckConstraint("record_version > 0", name="content_assets_record_version_check"),
    )
    op.create_index(
        "ix_content_assets_tenant_status",
        "content_assets",
        ["tenant_id", "status", "updated_at"],
    )
    op.create_index(
        "ix_content_assets_tenant_owner",
        "content_assets",
        ["tenant_id", "owner_membership_id", "status"],
    )
    op.create_index(
        "ix_content_assets_tenant_classification",
        "content_assets",
        ["tenant_id", "content_type", "language"],
    )

    op.create_table(
        "content_generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("content_request_id", "content_requests.id"),
        uuid_column("agent_run_id", "agent_runs.id"),
        uuid_column("agent_id", "agents.id"),
        uuid_column("agent_version_id", "agent_configurations.id"),
        sa.Column("provider", sa.String(120)),
        sa.Column("model", sa.String(120)),
        sa.Column("evidence_status", sa.String(20)),
        sa.Column(
            "retrieved_chunk_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("output_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "validation_summary",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column(
            "token_usage",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("estimated_cost", sa.Numeric(19, 6)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "agent_run_id"),
        sa.CheckConstraint(
            "evidence_status IS NULL OR evidence_status IN "
            "('sufficient','insufficient','conflicting')",
            name="content_generation_runs_evidence_check",
        ),
    )
    op.create_index(
        "ix_content_generation_runs_tenant_request",
        "content_generation_runs",
        ["tenant_id", "content_request_id", "created_at"],
    )

    op.create_table(
        "content_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("content_asset_id", "content_assets.id"),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("content_body", postgresql.JSONB(), nullable=False),
        sa.Column("plain_text", sa.Text(), nullable=False),
        sa.Column(
            "claims", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "citations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        uuid_column("generation_run_id", "content_generation_runs.id", nullable=True),
        uuid_column("based_on_version_id", "content_versions.id", nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        uuid_column("created_by", "tenant_memberships.id"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "content_asset_id", "version_number"),
        sa.CheckConstraint("version_number > 0", name="content_versions_number_check"),
        sa.CheckConstraint(
            "origin IN ('human','ai_generated','rollback')",
            name="content_versions_origin_check",
        ),
        sa.CheckConstraint("length(content_sha256) = 64", name="content_versions_sha_check"),
    )
    op.create_index(
        "ix_content_versions_tenant_asset",
        "content_versions",
        ["tenant_id", "content_asset_id", "version_number"],
    )

    op.create_foreign_key(
        "fk_content_assets_current_version_id",
        "content_assets",
        "content_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )
    op.create_foreign_key(
        "fk_content_assets_approved_version_id",
        "content_assets",
        "content_versions",
        ["approved_version_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )
    op.create_foreign_key(
        "fk_content_requests_result_asset_id",
        "content_requests",
        "content_assets",
        ["result_asset_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )
    op.create_foreign_key(
        "fk_content_generation_runs_output_version_id",
        "content_generation_runs",
        "content_versions",
        ["output_version_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )

    op.create_table(
        "content_approval_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("content_asset_id", "content_assets.id"),
        uuid_column("content_version_id", "content_versions.id"),
        sa.Column("decision_type", sa.String(30), nullable=False),
        uuid_column("decided_by", "tenant_memberships.id"),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "decision_type IN ('submitted','changes_requested','approved','rejected')",
            name="content_approval_decisions_type_check",
        ),
        sa.CheckConstraint(
            "length(content_sha256) = 64", name="content_approval_decisions_sha_check"
        ),
    )
    op.create_index(
        "ix_content_approval_decisions_tenant_asset",
        "content_approval_decisions",
        ["tenant_id", "content_asset_id", "created_at"],
    )

    op.create_table(
        "content_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        uuid_column("tenant_id", "tenants.id"),
        uuid_column("actor_membership_id", "tenant_memberships.id"),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        uuid_column("content_asset_id", "content_assets.id", nullable=True),
        uuid_column("content_version_id", "content_versions.id", nullable=True),
        uuid_column("content_request_id", "content_requests.id", nullable=True),
        uuid_column("content_generation_run_id", "content_generation_runs.id", nullable=True),
        sa.Column("outcome", sa.String(30), nullable=False, server_default="success"),
        sa.Column(
            "before_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "after_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "details",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_content_audit_logs_tenant_asset",
        "content_audit_logs",
        ["tenant_id", "content_asset_id", "created_at"],
    )
    op.create_index(
        "ix_content_audit_logs_tenant_request",
        "content_audit_logs",
        ["tenant_id", "content_request_id", "created_at"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    tenant_tables = (
        "content_requests",
        "content_assets",
        "content_generation_runs",
        "content_versions",
        "content_approval_decisions",
        "content_audit_logs",
    )
    for table_name in tenant_tables:
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY "{table_name}_tenant_isolation" ON "{table_name}" '
                f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
            )
        )

    op.execute(
        """
        CREATE FUNCTION prevent_content_history_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'governed content history is immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in ("content_versions", "content_approval_decisions", "content_audit_logs"):
        op.execute(
            sa.text(
                f'CREATE TRIGGER "{table_name}_immutable" '
                f'BEFORE UPDATE OR DELETE ON "{table_name}" '
                "FOR EACH ROW EXECUTE FUNCTION prevent_content_history_mutation()"
            )
        )


def downgrade() -> None:
    for table_name in ("content_versions", "content_approval_decisions", "content_audit_logs"):
        op.execute(sa.text(f'DROP TRIGGER IF EXISTS "{table_name}_immutable" ON "{table_name}"'))
    op.execute("DROP FUNCTION IF EXISTS prevent_content_history_mutation()")

    op.drop_table("content_audit_logs")
    op.drop_table("content_approval_decisions")
    op.drop_constraint(
        "fk_content_generation_runs_output_version_id",
        "content_generation_runs",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_content_requests_result_asset_id", "content_requests", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_content_assets_approved_version_id", "content_assets", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_content_assets_current_version_id", "content_assets", type_="foreignkey"
    )
    op.drop_table("content_versions")
    op.drop_table("content_generation_runs")
    op.drop_table("content_assets")
    op.drop_table("content_requests")
