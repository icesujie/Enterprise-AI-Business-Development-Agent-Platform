"""Align registry tenant foreign-key deletion policy with the ORM.

Revision ID: e27d4b90a1c5
Revises: 8c91f2a4d6e3
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e27d4b90a1c5"
down_revision: str | None = "8c91f2a4d6e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("agent_capability_bindings", "tenant_agent_activations"):
        constraint_name = f"{table_name}_tenant_id_fkey"
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            table_name,
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    for table_name in ("agent_capability_bindings", "tenant_agent_activations"):
        constraint_name = f"{table_name}_tenant_id_fkey"
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            table_name,
            "tenants",
            ["tenant_id"],
            ["id"],
        )
