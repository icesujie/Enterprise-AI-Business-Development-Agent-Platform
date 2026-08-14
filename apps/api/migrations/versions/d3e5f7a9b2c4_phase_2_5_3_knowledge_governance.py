"""Add the Phase 2.5.3 enterprise knowledge governance layer.

Revision ID: d3e5f7a9b2c4
Revises: a7d4c2e91f63
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d3e5f7a9b2c4"
down_revision: str | None = "a7d4c2e91f63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "managed_knowledge_documents_lifecycle_check",
        "managed_knowledge_documents",
        type_="check",
    )
    op.create_check_constraint(
        "managed_knowledge_documents_lifecycle_check",
        "managed_knowledge_documents",
        "lifecycle_status IN "
        "('draft','uploaded','processing','review','approved','published','active','archived')",
    )
    op.drop_constraint(
        "knowledge_document_versions_status_check",
        "knowledge_document_versions",
        type_="check",
    )
    op.execute(
        "UPDATE knowledge_document_versions SET status = 'approved' "
        "WHERE status IN ('published','superseded')"
    )
    op.execute("UPDATE knowledge_document_versions SET status = 'uploaded' WHERE status = 'draft'")
    op.create_check_constraint(
        "knowledge_document_versions_status_check",
        "knowledge_document_versions",
        "status IN "
        "('draft','uploaded','processing','review','approved','published','active',"
        "'archived','rejected','superseded')",
    )

    for column_name in ("current_version_id", "published_version_id", "active_version_id"):
        op.add_column(
            "managed_knowledge_documents",
            sa.Column(column_name, postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            f"fk_managed_knowledge_documents_{column_name}",
            "managed_knowledge_documents",
            "knowledge_document_versions",
            [column_name],
            ["id"],
            ondelete="RESTRICT",
            use_alter=True,
        )
    op.add_column(
        "managed_knowledge_documents",
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "managed_knowledge_documents",
        sa.Column(
            "published_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "managed_knowledge_documents", sa.Column("published_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "managed_knowledge_documents",
        sa.Column(
            "archived_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "managed_knowledge_documents", sa.Column("archived_at", sa.DateTime(timezone=True))
    )
    op.add_column("managed_knowledge_documents", sa.Column("archive_reason", sa.Text()))
    op.add_column("managed_knowledge_documents", sa.Column("restore_reason", sa.Text()))
    op.create_index(
        "ix_managed_knowledge_documents_tenant_pointers",
        "managed_knowledge_documents",
        ["tenant_id", "published_version_id", "active_version_id"],
    )

    op.add_column(
        "knowledge_document_versions",
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column(
        "knowledge_document_versions",
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "knowledge_document_versions", sa.Column("reviewed_at", sa.DateTime(timezone=True))
    )
    op.add_column("knowledge_document_versions", sa.Column("review_note", sa.Text()))
    op.add_column(
        "knowledge_document_versions",
        sa.Column(
            "restored_from_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "knowledge_document_versions",
        sa.Column("created_from_action", sa.String(30), nullable=False, server_default="upload"),
    )
    op.create_check_constraint(
        "knowledge_document_versions_review_check",
        "knowledge_document_versions",
        "review_status IN ('pending','approved','rejected')",
    )
    op.create_check_constraint(
        "knowledge_document_versions_origin_check",
        "knowledge_document_versions",
        "created_from_action IN ('upload','rollback')",
    )

    op.add_column(
        "knowledge_document_agent_bindings",
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "knowledge_document_agent_bindings",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.execute(
        "UPDATE managed_knowledge_documents d SET current_version_id = v.id "
        "FROM knowledge_document_versions v "
        "WHERE v.tenant_id = d.tenant_id AND v.document_id = d.id "
        "AND v.version_number = d.current_version_number"
    )
    op.execute(
        "UPDATE managed_knowledge_documents SET published_version_id = current_version_id, "
        "active_version_id = current_version_id WHERE lifecycle_status = 'active'"
    )
    op.execute(
        "UPDATE knowledge_document_versions v SET review_status = 'approved', "
        "reviewed_by = d.approved_by, reviewed_at = d.approved_at, review_note = d.review_note "
        "FROM managed_knowledge_documents d WHERE v.document_id = d.id "
        "AND v.version_number = d.current_version_number "
        "AND v.status IN ('approved','active','archived')"
    )
    op.execute(
        "UPDATE knowledge_document_versions SET review_status = 'rejected' "
        "WHERE status = 'rejected'"
    )

    op.create_table(
        "knowledge_audit_logs",
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
            sa.ForeignKey("managed_knowledge_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("before_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("after_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_knowledge_audit_logs_tenant_document",
        "knowledge_audit_logs",
        ["tenant_id", "document_id", "created_at"],
    )
    op.create_index(
        "ix_knowledge_audit_logs_tenant_version",
        "knowledge_audit_logs",
        ["tenant_id", "document_version_id", "created_at"],
    )
    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    op.execute('ALTER TABLE "knowledge_audit_logs" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "knowledge_audit_logs" FORCE ROW LEVEL SECURITY')
    op.execute(
        sa.text(
            'CREATE POLICY "knowledge_audit_logs_tenant_isolation" '
            'ON "knowledge_audit_logs" '
            f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
        )
    )


def downgrade() -> None:
    op.drop_table("knowledge_audit_logs")
    op.drop_column("knowledge_document_agent_bindings", "updated_at")
    op.drop_column("knowledge_document_agent_bindings", "updated_by")
    op.drop_constraint(
        "knowledge_document_versions_origin_check", "knowledge_document_versions", type_="check"
    )
    op.drop_constraint(
        "knowledge_document_versions_review_check", "knowledge_document_versions", type_="check"
    )
    for column_name in (
        "created_from_action",
        "restored_from_version_id",
        "review_note",
        "reviewed_at",
        "reviewed_by",
        "review_status",
    ):
        op.drop_column("knowledge_document_versions", column_name)
    op.drop_index(
        "ix_managed_knowledge_documents_tenant_pointers",
        table_name="managed_knowledge_documents",
    )
    for column_name in (
        "restore_reason",
        "archive_reason",
        "archived_at",
        "archived_by",
        "published_at",
        "published_by",
        "updated_by",
    ):
        op.drop_column("managed_knowledge_documents", column_name)
    for column_name in ("active_version_id", "published_version_id", "current_version_id"):
        op.drop_constraint(
            f"fk_managed_knowledge_documents_{column_name}",
            "managed_knowledge_documents",
            type_="foreignkey",
        )
        op.drop_column("managed_knowledge_documents", column_name)
    op.drop_constraint(
        "knowledge_document_versions_status_check",
        "knowledge_document_versions",
        type_="check",
    )
    op.create_check_constraint(
        "knowledge_document_versions_status_check",
        "knowledge_document_versions",
        "status IN ('uploaded','processing','review','approved','active','archived','rejected')",
    )
    op.drop_constraint(
        "managed_knowledge_documents_lifecycle_check",
        "managed_knowledge_documents",
        type_="check",
    )
    op.execute(
        "UPDATE managed_knowledge_documents SET lifecycle_status = 'approved' "
        "WHERE lifecycle_status = 'published'"
    )
    op.create_check_constraint(
        "managed_knowledge_documents_lifecycle_check",
        "managed_knowledge_documents",
        "lifecycle_status IN "
        "('draft','uploaded','processing','review','approved','active','archived')",
    )
