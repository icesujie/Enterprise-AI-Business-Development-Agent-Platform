"""Establish the migration baseline without business tables.

Revision ID: 20260808_0001
Revises:
Create Date: 2026-08-08
"""

from collections.abc import Sequence

revision: str = "20260808_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the empty M1 migration baseline."""


def downgrade() -> None:
    """Return to the pre-M1 migration state."""
