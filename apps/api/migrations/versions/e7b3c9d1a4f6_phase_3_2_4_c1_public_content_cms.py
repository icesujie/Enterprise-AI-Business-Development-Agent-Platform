"""Add governed public content CMS persistence and RLS.

Revision ID: e7b3c9d1a4f6
Revises: d4e8f2a6b731
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7b3c9d1a4f6"
down_revision: str | None = "d4e8f2a6b731"
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
        "public_content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("page_type", sa.String(30), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("locale", sa.String(20), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("seo_title", sa.String(250), nullable=False),
        sa.Column("seo_description", sa.String(500), nullable=False),
        sa.Column("canonical_path", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("published_version_id", postgresql.UUID(as_uuid=True)),
        membership_column("created_by"),
        membership_column("approved_by", nullable=True),
        membership_column("published_by", nullable=True),
        membership_column("archived_by", nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("archive_reason", sa.Text()),
        sa.UniqueConstraint(
            "tenant_id", "page_type", "slug", "locale", name="uq_public_content_route_locale"
        ),
        sa.UniqueConstraint(
            "tenant_id", "canonical_path", "locale", name="uq_public_content_canonical_locale"
        ),
        sa.CheckConstraint(
            "page_type IN ('solution','industry','case_study','guide')",
            name="public_content_items_page_type_check",
        ),
        sa.CheckConstraint("locale IN ('en','zh-CN')", name="public_content_items_locale_check"),
        sa.CheckConstraint(
            "status IN ('draft','review','approved','published','archived')",
            name="public_content_items_status_check",
        ),
        sa.CheckConstraint("record_version > 0", name="public_content_items_version_check"),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="public_content_items_slug_check"
        ),
    )
    op.create_index(
        "ix_public_content_items_tenant_status",
        "public_content_items",
        ["tenant_id", "status", "updated_at"],
    )
    op.create_index(
        "ix_public_content_items_tenant_type_locale",
        "public_content_items",
        ["tenant_id", "page_type", "locale", "status"],
    )

    op.create_table(
        "public_content_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "public_content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("seo_title", sa.String(250), nullable=False),
        sa.Column("seo_description", sa.String(500), nullable=False),
        sa.Column("structured_content", postgresql.JSONB(), nullable=False),
        sa.Column(
            "media_references",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("source_reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_filename", sa.String(500)),
        sa.Column("source_checksum", sa.String(64)),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column(
            "based_on_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_versions.id", ondelete="RESTRICT"),
        ),
        membership_column("created_by"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "public_content_item_id",
            "version_number",
            name="uq_public_content_version_number",
        ),
        sa.CheckConstraint("version_number > 0", name="public_content_versions_number_check"),
        sa.CheckConstraint(
            "origin IN ('human','ai_draft','imported','rollback')",
            name="public_content_versions_origin_check",
        ),
        sa.CheckConstraint(
            "source_type IN ('manual','knowledge_version','marketing_content_version',"
            "'docx_import','pdf_import','html_import','text_import')",
            name="public_content_versions_source_type_check",
        ),
        sa.CheckConstraint("length(content_sha256) = 64", name="public_content_versions_sha_check"),
        sa.CheckConstraint(
            "source_checksum IS NULL OR length(source_checksum) = 64",
            name="public_content_versions_source_sha_check",
        ),
    )
    op.create_index(
        "ix_public_content_versions_tenant_item",
        "public_content_versions",
        ["tenant_id", "public_content_item_id", "version_number"],
    )

    for pointer in ("current", "approved", "published"):
        op.create_foreign_key(
            f"fk_public_content_items_{pointer}_version_id",
            "public_content_items",
            "public_content_versions",
            [f"{pointer}_version_id"],
            ["id"],
            ondelete="RESTRICT",
            use_alter=True,
        )

    op.create_table(
        "public_content_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "public_content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "public_content_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decision_type", sa.String(30), nullable=False),
        membership_column("decided_by"),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "decision_type IN ('submitted','changes_requested','approved','rejected','published')",
            name="public_content_decisions_type_check",
        ),
        sa.CheckConstraint(
            "length(content_sha256) = 64", name="public_content_decisions_sha_check"
        ),
    )
    op.create_index(
        "ix_public_content_decisions_tenant_item",
        "public_content_decisions",
        ["tenant_id", "public_content_item_id", "created_at"],
    )

    op.create_table(
        "public_content_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        membership_column("actor_membership_id"),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column(
            "public_content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "public_content_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_content_versions.id", ondelete="RESTRICT"),
        ),
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
        "ix_public_content_audit_tenant_item",
        "public_content_audit_logs",
        ["tenant_id", "public_content_item_id", "created_at"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    tenant_tables = (
        "public_content_items",
        "public_content_versions",
        "public_content_decisions",
        "public_content_audit_logs",
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
        CREATE FUNCTION prevent_public_content_history_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'public content history is immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in (
        "public_content_versions",
        "public_content_decisions",
        "public_content_audit_logs",
    ):
        op.execute(
            sa.text(
                f'CREATE TRIGGER "{table_name}_immutable" '
                f'BEFORE UPDATE OR DELETE ON "{table_name}" '
                "FOR EACH ROW EXECUTE FUNCTION prevent_public_content_history_mutation()"
            )
        )


def downgrade() -> None:
    for table_name in (
        "public_content_versions",
        "public_content_decisions",
        "public_content_audit_logs",
    ):
        op.execute(sa.text(f'DROP TRIGGER IF EXISTS "{table_name}_immutable" ON "{table_name}"'))
    op.execute("DROP FUNCTION IF EXISTS prevent_public_content_history_mutation()")
    op.drop_table("public_content_audit_logs")
    op.drop_table("public_content_decisions")
    for pointer in ("published", "approved", "current"):
        op.drop_constraint(
            f"fk_public_content_items_{pointer}_version_id",
            "public_content_items",
            type_="foreignkey",
        )
    op.drop_table("public_content_versions")
    op.drop_table("public_content_items")
