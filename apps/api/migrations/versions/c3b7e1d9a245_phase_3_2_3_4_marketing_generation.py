"""Enable governed Marketing Agent generation in development.

Revision ID: c3b7e1d9a245
Revises: a91e4c7b2d65
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3b7e1d9a245"
down_revision: str | None = "a91e4c7b2d65"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONFIG_ID = "50000000-0000-4000-8000-000000000003"
DEVELOPMENT_ACTIVATION_ID = "63000000-0000-4000-8000-000000000003"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE agent_configurations
           SET runtime_config = runtime_config || jsonb_build_object(
               'execution_enabled', true, 'generation_enabled', true
           )
         WHERE id = '{CONFIG_ID}'
        """
    )
    op.execute(
        f"""
        UPDATE tenant_agent_activations
           SET reason = 'Development generation enabled; production pending'
         WHERE id = '{DEVELOPMENT_ACTIVATION_ID}'
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE agent_configurations
           SET runtime_config = runtime_config || jsonb_build_object(
               'execution_enabled', false, 'generation_enabled', false
           )
         WHERE id = '{CONFIG_ID}'
        """
    )
    op.execute(
        f"""
        UPDATE tenant_agent_activations
           SET reason = 'Policy validation only; generation disabled'
         WHERE id = '{DEVELOPMENT_ACTIVATION_ID}'
        """
    )
