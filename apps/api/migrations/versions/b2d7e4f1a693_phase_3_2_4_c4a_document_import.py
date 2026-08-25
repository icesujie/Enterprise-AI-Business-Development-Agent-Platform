"""Add governed public-content document imports.

Revision ID: b2d7e4f1a693
Revises: f9c4d2a7b816
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2d7e4f1a693"
down_revision: str | None = "f9c4d2a7b816"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "public_content_imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("storage_provider", sa.String(40), nullable=False, server_default="local"),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("failure_reason", sa.String(500)),
        sa.Column(
            "extraction_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "extraction_result",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "extracted_media_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "source_type IN ('docx','pdf','html','txt','markdown')",
            name="public_content_imports_source_type_check",
        ),
        sa.CheckConstraint(
            "processing_status IN ('uploaded','processing','completed','failed')",
            name="public_content_imports_status_check",
        ),
        sa.CheckConstraint("file_size > 0", name="public_content_imports_size_check"),
        sa.CheckConstraint("length(checksum) = 64", name="public_content_imports_sha_check"),
    )
    op.create_index(
        "ix_public_content_imports_tenant_status",
        "public_content_imports",
        ["tenant_id", "processing_status", "created_at"],
    )
    op.create_table(
        "public_content_import_audit_logs",
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
            "actor_membership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_memberships.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(80), nullable=False),
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
        "ix_public_content_import_audit_tenant_import",
        "public_content_import_audit_logs",
        ["tenant_id", "public_content_import_id", "created_at"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in ("public_content_imports", "public_content_import_audit_logs"):
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
        CREATE FUNCTION prevent_public_content_import_audit_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'public content import audit history is immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        'CREATE TRIGGER "public_content_import_audit_immutable" '
        'BEFORE UPDATE OR DELETE ON "public_content_import_audit_logs" '
        "FOR EACH ROW EXECUTE FUNCTION prevent_public_content_import_audit_mutation()"
    )


def downgrade() -> None:
    op.execute(
        'DROP TRIGGER IF EXISTS "public_content_import_audit_immutable" '
        'ON "public_content_import_audit_logs"'
    )
    op.execute("DROP FUNCTION IF EXISTS prevent_public_content_import_audit_mutation()")
    op.drop_table("public_content_import_audit_logs")
    op.drop_table("public_content_imports")
