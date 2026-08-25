"""Allow governed Product pages in Public Content.

Revision ID: d8f1c4a7b902
Revises: c5e8a1d4f720
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d8f1c4a7b902"
down_revision: str | None = "c5e8a1d4f720"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "public_content_items_page_type_check",
        "public_content_items",
        type_="check",
    )
    op.create_check_constraint(
        "public_content_items_page_type_check",
        "public_content_items",
        "page_type IN ('solution','industry','case_study','guide','product')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "public_content_items_page_type_check",
        "public_content_items",
        type_="check",
    )
    op.create_check_constraint(
        "public_content_items_page_type_check",
        "public_content_items",
        "page_type IN ('solution','industry','case_study','guide')",
    )
