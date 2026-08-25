"""Add governed public-content structuring runs.

Revision ID: c5e8a1d4f720
Revises: b2d7e4f1a693
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c5e8a1d4f720"
down_revision: str | None = "b2d7e4f1a693"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "public_content_structuring_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "public_content_import_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_imports.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("selected_page_type", sa.String(30), nullable=False),
        sa.Column("recommended_page_type", sa.String(30)),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("outcome", sa.String(40)),
        sa.Column(
            "result",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "missing_fields",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("failure_reason", sa.String(500)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "selected_page_type IN ('solution','industry','case_study','guide')",
            name="public_content_structuring_selected_type_check",
        ),
        sa.CheckConstraint(
            "recommended_page_type IS NULL OR recommended_page_type IN "
            "('solution','industry','case_study','guide')",
            name="public_content_structuring_recommended_type_check",
        ),
        sa.CheckConstraint(
            "locale IN ('en','zh-CN')", name="public_content_structuring_locale_check"
        ),
        sa.CheckConstraint(
            "status IN ('running','completed','failed')",
            name="public_content_structuring_status_check",
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN "
            "('ready','requires_human_input','insufficient_source')",
            name="public_content_structuring_outcome_check",
        ),
    )
    op.create_index(
        "ix_public_content_structuring_tenant_import",
        "public_content_structuring_runs",
        ["tenant_id", "public_content_import_id", "created_at"],
    )
    expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    op.execute(sa.text('ALTER TABLE "public_content_structuring_runs" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "public_content_structuring_runs" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            'CREATE POLICY "public_content_structuring_runs_tenant_isolation" '
            'ON "public_content_structuring_runs" '
            f"USING ({expression}) WITH CHECK ({expression})"
        )
    )


def downgrade() -> None:
    op.drop_table("public_content_structuring_runs")
