"""Add the Phase 2.5.1 enterprise knowledge management control plane.

Revision ID: 6b2a8e4d1c90
Revises: 9f31c6a7d2b4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6b2a8e4d1c90"
down_revision: str | None = "9f31c6a7d2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "domain_package_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domain_packages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("collection_key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("collection_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("tenant_id", "collection_key"),
        sa.CheckConstraint(
            "status IN ('active','archived')", name="knowledge_collections_status_check"
        ),
    )
    op.create_index(
        "ix_knowledge_collections_tenant_domain",
        "knowledge_collections",
        ["tenant_id", "domain_package_id", "status"],
    )

    op.create_table(
        "managed_knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "domain_package_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domain_packages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "collection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_collections.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=False),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("approval_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("document_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("review_note", sa.Text()),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(
            "lifecycle_status IN "
            "('draft','uploaded','processing','review','approved','active','archived')",
            name="managed_knowledge_documents_lifecycle_check",
        ),
        sa.CheckConstraint(
            "approval_status IN ('pending','approved','rejected')",
            name="managed_knowledge_documents_approval_check",
        ),
        sa.CheckConstraint(
            "current_version_number > 0", name="managed_knowledge_documents_version_check"
        ),
    )
    op.create_index(
        "ix_managed_knowledge_documents_tenant_collection",
        "managed_knowledge_documents",
        ["tenant_id", "collection_id", "lifecycle_status"],
    )
    op.create_index(
        "ix_managed_knowledge_documents_tenant_search",
        "managed_knowledge_documents",
        ["tenant_id", "domain_package_id", "agent_id", "updated_at"],
    )

    op.create_table(
        "knowledge_document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(120), nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("version_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "document_id", "version_number"),
        sa.UniqueConstraint("tenant_id", "object_key"),
        sa.CheckConstraint("byte_size > 0", name="knowledge_document_versions_size_check"),
        sa.CheckConstraint(
            "status IN "
            "('uploaded','processing','review','approved','active','archived','rejected')",
            name="knowledge_document_versions_status_check",
        ),
    )
    op.create_index(
        "ix_knowledge_document_versions_tenant_document",
        "knowledge_document_versions",
        ["tenant_id", "document_id", "version_number"],
    )

    op.create_table(
        "knowledge_document_agent_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="enabled"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "document_id", "agent_id"),
        sa.CheckConstraint(
            "status IN ('enabled','disabled')",
            name="knowledge_document_agent_bindings_status_check",
        ),
    )
    op.create_index(
        "ix_knowledge_document_agent_bindings_access",
        "knowledge_document_agent_bindings",
        ["tenant_id", "agent_id", "status"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in (
        "knowledge_collections",
        "managed_knowledge_documents",
        "knowledge_document_versions",
        "knowledge_document_agent_bindings",
    ):
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY "{table_name}_tenant_isolation" ON "{table_name}" '
                f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
            )
        )


def downgrade() -> None:
    for table_name in (
        "knowledge_document_agent_bindings",
        "knowledge_document_versions",
        "managed_knowledge_documents",
        "knowledge_collections",
    ):
        op.drop_table(table_name)
