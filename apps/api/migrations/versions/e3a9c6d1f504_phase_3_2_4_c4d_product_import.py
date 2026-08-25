"""Allow governed Product structuring and preserve candidate traceability.

Revision ID: e3a9c6d1f504
Revises: d8f1c4a7b902
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e3a9c6d1f504"
down_revision: str | None = "d8f1c4a7b902"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "public_content_structuring_selected_type_check",
        "public_content_structuring_runs",
        type_="check",
    )
    op.drop_constraint(
        "public_content_structuring_recommended_type_check",
        "public_content_structuring_runs",
        type_="check",
    )
    op.create_check_constraint(
        "public_content_structuring_selected_type_check",
        "public_content_structuring_runs",
        "selected_page_type IN ('solution','industry','case_study','guide','product')",
    )
    op.create_check_constraint(
        "public_content_structuring_recommended_type_check",
        "public_content_structuring_runs",
        "recommended_page_type IS NULL OR recommended_page_type IN "
        "('solution','industry','case_study','guide','product')",
    )
    op.add_column(
        "public_content_versions",
        sa.Column("source_structuring_run_id", postgresql.UUID(as_uuid=True)),
    )
    op.add_column(
        "public_content_versions",
        sa.Column("source_candidate_key", sa.String(40)),
    )
    op.create_foreign_key(
        "fk_public_content_versions_source_structuring_run",
        "public_content_versions",
        "public_content_structuring_runs",
        ["source_structuring_run_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_public_content_versions_source_structuring_run",
        "public_content_versions",
        type_="foreignkey",
    )
    op.drop_column("public_content_versions", "source_candidate_key")
    op.drop_column("public_content_versions", "source_structuring_run_id")
    op.drop_constraint(
        "public_content_structuring_recommended_type_check",
        "public_content_structuring_runs",
        type_="check",
    )
    op.drop_constraint(
        "public_content_structuring_selected_type_check",
        "public_content_structuring_runs",
        type_="check",
    )
    op.create_check_constraint(
        "public_content_structuring_selected_type_check",
        "public_content_structuring_runs",
        "selected_page_type IN ('solution','industry','case_study','guide')",
    )
    op.create_check_constraint(
        "public_content_structuring_recommended_type_check",
        "public_content_structuring_runs",
        "recommended_page_type IS NULL OR recommended_page_type IN "
        "('solution','industry','case_study','guide')",
    )
