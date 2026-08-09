"""M5 opportunity pipeline.

Revision ID: 7f3a21c942d0
Revises: 5d72a9b889f1
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7f3a21c942d0"
down_revision: str | None = "5d72a9b889f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE opportunities SET stage = 'discovery' WHERE stage = 'qualification'")
    )
    op.alter_column("opportunities", "stage", server_default="discovery")
    op.create_check_constraint(
        "opportunities_stage_check",
        "opportunities",
        "stage IN ('discovery','requirements_confirmed','proposal','negotiation','won','lost')",
    )


def downgrade() -> None:
    op.drop_constraint("opportunities_stage_check", "opportunities", type_="check")
    op.alter_column("opportunities", "stage", server_default="qualification")
