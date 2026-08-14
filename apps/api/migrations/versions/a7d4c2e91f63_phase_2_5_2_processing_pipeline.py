"""Add the Phase 2.5.2 managed knowledge processing pipeline.

Revision ID: a7d4c2e91f63
Revises: 6b2a8e4d1c90
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

revision: str = "a7d4c2e91f63"
down_revision: str | None = "6b2a8e4d1c90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "managed_knowledge_documents",
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="uploaded"),
    )
    op.create_check_constraint(
        "managed_knowledge_documents_processing_check",
        "managed_knowledge_documents",
        "processing_status IN ('uploaded','processing','completed','failed')",
    )

    op.create_table(
        "knowledge_processing_runs",
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
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("extractor_version", sa.String(40), nullable=False, server_default="extract_v2"),
        sa.Column("chunking_version", sa.String(40), nullable=False, server_default="chunk_v1"),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False),
        sa.Column("embedding_provider", sa.String(80), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "source_metadata_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
            "status IN ('uploaded','processing','completed','failed')",
            name="knowledge_processing_runs_status_check",
        ),
        sa.CheckConstraint(
            "chunk_size > 0 AND chunk_overlap >= 0 AND chunk_overlap < chunk_size",
            name="knowledge_processing_runs_chunking_check",
        ),
        sa.CheckConstraint(
            "embedding_dimensions = 1536",
            name="knowledge_processing_runs_dimensions_check",
        ),
    )
    op.create_index(
        "ix_knowledge_processing_runs_tenant_document",
        "knowledge_processing_runs",
        ["tenant_id", "document_id", "created_at"],
    )
    op.create_index(
        "ix_knowledge_processing_runs_tenant_status",
        "knowledge_processing_runs",
        ["tenant_id", "status", "created_at"],
    )

    op.create_table(
        "managed_knowledge_chunks",
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
            nullable=False,
        ),
        sa.Column(
            "collection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_collections.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_document_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "processing_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_processing_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("section_title", sa.String(300)),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("citation_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("embedding", VECTOR(1536), nullable=False),
        sa.Column("embedding_provider", sa.String(80), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "document_version_id", "agent_id", "chunk_index"),
    )
    op.create_index(
        "ix_managed_knowledge_chunks_access",
        "managed_knowledge_chunks",
        ["tenant_id", "domain_package_id", "agent_id", "document_id"],
    )
    op.create_index(
        "ix_managed_knowledge_chunks_version",
        "managed_knowledge_chunks",
        ["tenant_id", "document_version_id", "chunk_index"],
    )
    op.execute(
        "CREATE INDEX ix_managed_knowledge_chunks_embedding_hnsw "
        "ON managed_knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in ("knowledge_processing_runs", "managed_knowledge_chunks"):
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY "{table_name}_tenant_isolation" ON "{table_name}" '
                f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
            )
        )


def downgrade() -> None:
    op.drop_table("managed_knowledge_chunks")
    op.drop_table("knowledge_processing_runs")
    op.drop_constraint(
        "managed_knowledge_documents_processing_check",
        "managed_knowledge_documents",
        type_="check",
    )
    op.drop_column("managed_knowledge_documents", "processing_status")
