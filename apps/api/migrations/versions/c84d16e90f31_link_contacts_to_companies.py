"""Index contacts by company for CRM relationship queries.

Revision ID: c84d16e90f31
Revises: 7f3a21c942d0
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c84d16e90f31"
down_revision: str | None = "7f3a21c942d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_contacts_tenant_organization",
        "contacts",
        ["tenant_id", "organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_contacts_tenant_organization", table_name="contacts")
