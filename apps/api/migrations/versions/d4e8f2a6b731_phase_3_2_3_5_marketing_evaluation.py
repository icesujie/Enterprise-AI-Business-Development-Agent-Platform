"""Add immutable human marketing review feedback.

Revision ID: d4e8f2a6b731
Revises: c3b7e1d9a245
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e8f2a6b731"
down_revision: str | None = "c3b7e1d9a245"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_review_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "content_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "content_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_membership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("categories", postgresql.JSONB(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "length(content_sha256) = 64", name="content_review_feedback_sha_check"
        ),
    )
    op.create_index(
        "ix_content_review_feedback_tenant_asset",
        "content_review_feedback",
        ["tenant_id", "content_asset_id", "created_at"],
    )
    op.create_index(
        "ix_content_review_feedback_tenant_version",
        "content_review_feedback",
        ["tenant_id", "content_version_id", "created_at"],
    )
    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    op.execute('ALTER TABLE "content_review_feedback" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "content_review_feedback" FORCE ROW LEVEL SECURITY')
    op.execute(
        sa.text(
            'CREATE POLICY "content_review_feedback_tenant_isolation" '
            'ON "content_review_feedback" '
            f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
        )
    )
    op.execute(
        'CREATE TRIGGER "content_review_feedback_immutable" '
        'BEFORE UPDATE OR DELETE ON "content_review_feedback" '
        "FOR EACH ROW EXECUTE FUNCTION prevent_content_history_mutation()"
    )


def downgrade() -> None:
    op.execute(
        'DROP TRIGGER IF EXISTS "content_review_feedback_immutable" '
        'ON "content_review_feedback"'
    )
    op.drop_table("content_review_feedback")
