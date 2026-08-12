"""Add the Phase 2.5 tenant-scoped knowledge foundation.

Revision ID: 9f31c6a7d2b4
Revises: 4a68c3d2f901
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

revision: str = "9f31c6a7d2b4"
down_revision: str | None = "4a68c3d2f901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="manual_upload"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
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
        sa.UniqueConstraint("tenant_id", "source_key"),
        sa.CheckConstraint(
            "source_type IN ('manual_upload','approved_import')",
            name="knowledge_sources_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('active','disabled')",
            name="knowledge_sources_status_check",
        ),
    )
    op.create_index(
        "ix_knowledge_sources_tenant_status", "knowledge_sources", ["tenant_id", "status"]
    )
    op.create_table(
        "knowledge_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
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
            nullable=False,
        ),
        sa.Column("knowledge_category", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="disabled"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "source_id", "domain_package_id", "agent_id"),
        sa.CheckConstraint(
            "status IN ('enabled','disabled')",
            name="knowledge_bindings_status_check",
        ),
    )
    op.create_index(
        "ix_knowledge_bindings_access",
        "knowledge_bindings",
        ["tenant_id", "agent_id", "domain_package_id", "status"],
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(120), nullable=False),
        sa.Column("language", sa.String(20), nullable=False, server_default="en"),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("approval_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("ingestion_status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
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
        sa.UniqueConstraint("tenant_id", "source_id", "content_sha256"),
        sa.UniqueConstraint("tenant_id", "object_key"),
        sa.CheckConstraint(
            "approval_status IN ('pending','approved','rejected','retired')",
            name="knowledge_documents_approval_check",
        ),
        sa.CheckConstraint(
            "ingestion_status IN ('not_started','queued','processing','ready','failed')",
            name="knowledge_documents_ingestion_check",
        ),
        sa.CheckConstraint("byte_size > 0", name="knowledge_documents_size_check"),
    )
    op.create_index(
        "ix_knowledge_documents_tenant_source_status",
        "knowledge_documents",
        ["tenant_id", "source_id", "approval_status", "ingestion_status"],
    )
    op.create_table(
        "knowledge_ingestion_runs",
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
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("extraction_version", sa.String(40), nullable=False, server_default="extract_v1"),
        sa.Column("chunking_version", sa.String(40), nullable=False, server_default="chunk_v1"),
        sa.Column("embedding_provider", sa.String(80), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message_safe", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('queued','processing','succeeded','failed')",
            name="knowledge_ingestion_runs_status_check",
        ),
    )
    op.create_index(
        "ix_knowledge_ingestion_runs_tenant_status",
        "knowledge_ingestion_runs",
        ["tenant_id", "status", "created_at"],
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingestion_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_ingestion_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("section_title", sa.String(300)),
        sa.Column("citation_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("embedding", VECTOR(1536), nullable=False),
        sa.Column("embedding_provider", sa.String(80), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "document_id", "chunk_index"),
    )
    op.create_index(
        "ix_knowledge_chunks_tenant_document",
        "knowledge_chunks",
        ["tenant_id", "document_id", "chunk_index"],
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding_hnsw ON knowledge_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in (
        "knowledge_sources",
        "knowledge_bindings",
        "knowledge_documents",
        "knowledge_ingestion_runs",
        "knowledge_chunks",
    ):
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY tenant_isolation ON "{table_name}" '
                f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
            )
        )

    # Retrieval infrastructure is available only to the Sari Arta configuration.
    op.execute(
        "UPDATE agent_capabilities SET status = 'available' "
        "WHERE capability_key = 'approved_knowledge_retrieval'"
    )
    op.execute(
        "UPDATE agent_capability_bindings SET status = 'available' "
        "WHERE agent_configuration_id = '50000000-0000-4000-8000-000000000001' "
        "AND capability_id = (SELECT id FROM agent_capabilities "
        "WHERE capability_key = 'approved_knowledge_retrieval')"
    )
    op.execute(
        "UPDATE agent_configurations SET runtime_config = "
        "jsonb_set(runtime_config, '{knowledge_enabled}', 'true'::jsonb, true) "
        "WHERE id = '50000000-0000-4000-8000-000000000001'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE agent_configurations SET runtime_config = "
        "jsonb_set(runtime_config, '{knowledge_enabled}', 'false'::jsonb, true) "
        "WHERE id = '50000000-0000-4000-8000-000000000001'"
    )
    op.execute(
        "UPDATE agent_capability_bindings SET status = 'planned' "
        "WHERE agent_configuration_id = '50000000-0000-4000-8000-000000000001' "
        "AND capability_id = (SELECT id FROM agent_capabilities "
        "WHERE capability_key = 'approved_knowledge_retrieval')"
    )
    op.execute(
        "UPDATE agent_capabilities SET status = 'planned' "
        "WHERE capability_key = 'approved_knowledge_retrieval'"
    )
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.drop_index("ix_knowledge_chunks_tenant_document", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_index(
        "ix_knowledge_ingestion_runs_tenant_status", table_name="knowledge_ingestion_runs"
    )
    op.drop_table("knowledge_ingestion_runs")
    op.drop_index("ix_knowledge_documents_tenant_source_status", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_knowledge_bindings_access", table_name="knowledge_bindings")
    op.drop_table("knowledge_bindings")
    op.drop_index("ix_knowledge_sources_tenant_status", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
