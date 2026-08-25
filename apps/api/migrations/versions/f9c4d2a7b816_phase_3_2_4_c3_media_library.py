"""Add governed media library persistence and RLS.

Revision ID: f9c4d2a7b816
Revises: e7b3c9d1a4f6
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f9c4d2a7b816"
down_revision: str | None = "e7b3c9d1a4f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def membership_column(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("tenant_memberships.id", ondelete="RESTRICT"),
        nullable=nullable,
    )


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("media_type", sa.String(30), nullable=False, server_default="image"),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(80), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("storage_provider", sa.String(40), nullable=False, server_default="local"),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("alt_text", sa.String(500), nullable=False),
        sa.Column("caption", sa.Text()),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="private"),
        sa.Column("public_use_status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual_upload"),
        sa.Column("source_reference_id", postgresql.UUID(as_uuid=True)),
        membership_column("uploaded_by"),
        membership_column("approved_by", nullable=True),
        membership_column("revoked_by", nullable=True),
        membership_column("archived_by", nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "storage_key", name="uq_media_assets_storage_key"),
        sa.CheckConstraint("media_type IN ('image')", name="media_assets_type_check"),
        sa.CheckConstraint(
            "mime_type IN ('image/jpeg','image/png','image/webp')",
            name="media_assets_mime_check",
        ),
        sa.CheckConstraint("file_size > 0", name="media_assets_size_check"),
        sa.CheckConstraint("width > 0 AND height > 0", name="media_assets_dimensions_check"),
        sa.CheckConstraint("length(checksum) = 64", name="media_assets_checksum_check"),
        sa.CheckConstraint(
            "visibility IN ('private','public')", name="media_assets_visibility_check"
        ),
        sa.CheckConstraint(
            "public_use_status IN ('uploaded','review','approved','revoked','archived')",
            name="media_assets_public_use_status_check",
        ),
        sa.CheckConstraint(
            "source_type IN ('manual_upload','docx_import','pdf_import','html_import')",
            name="media_assets_source_type_check",
        ),
        sa.CheckConstraint("record_version > 0", name="media_assets_version_check"),
    )
    op.create_index(
        "ix_media_assets_tenant_status",
        "media_assets",
        ["tenant_id", "public_use_status", "updated_at"],
    )
    op.create_index("ix_media_assets_tenant_checksum", "media_assets", ["tenant_id", "checksum"])

    op.create_table(
        "media_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "media_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("media_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        membership_column("actor_membership_id"),
        sa.Column("action", sa.String(80), nullable=False),
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
        "ix_media_audit_tenant_asset",
        "media_audit_logs",
        ["tenant_id", "media_asset_id", "created_at"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in ("media_assets", "media_audit_logs"):
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
        CREATE FUNCTION prevent_media_audit_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'media audit history is immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        'CREATE TRIGGER "media_audit_logs_immutable" '
        'BEFORE UPDATE OR DELETE ON "media_audit_logs" '
        "FOR EACH ROW EXECUTE FUNCTION prevent_media_audit_mutation()"
    )


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS "media_audit_logs_immutable" ON "media_audit_logs"')
    op.execute("DROP FUNCTION IF EXISTS prevent_media_audit_mutation()")
    op.drop_table("media_audit_logs")
    op.drop_table("media_assets")
