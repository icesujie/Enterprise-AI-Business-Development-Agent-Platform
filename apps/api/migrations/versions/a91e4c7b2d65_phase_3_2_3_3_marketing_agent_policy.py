# ruff: noqa: E501, RUF001 -- migration SQL contains stable multilingual registry records.

"""Register the governed Marketing Content Agent and policy capability.

Revision ID: a91e4c7b2d65
Revises: f6a1c9d2e4b7
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a91e4c7b2d65"
down_revision: str | None = "f6a1c9d2e4b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_ID = "10000000-0000-4000-8000-000000000001"
DOMAIN_ID = "60000000-0000-4000-8000-000000000001"
AGENT_ID = "61000000-0000-4000-8000-000000000003"
CONFIG_ID = "50000000-0000-4000-8000-000000000003"
CAPABILITY_ID = "62000000-0000-4000-8000-000000000006"
DEVELOPMENT_ACTIVATION_ID = "63000000-0000-4000-8000-000000000003"
PRODUCTION_ACTIVATION_ID = "63000000-0000-4000-8000-000000000004"


def upgrade() -> None:
    _execute_statements(
        f"""
        INSERT INTO agents
            (id, domain_package_id, agent_key, display_name, description, agent_type,
             implementation_key, supported_locales, response_locale_policy, status)
        VALUES
            ('{AGENT_ID}', '{DOMAIN_ID}', 'commercial_kitchen.marketing_content',
             '{{"en":"Sari Arta Marketing Content Agent","zh-CN":"Sari Arta 营销内容智能体"}}',
             '{{"en":"Prepares governed B2B marketing drafts only from explicitly eligible public knowledge.","zh-CN":"仅依据明确合格的公开知识准备受治理的 B2B 营销草稿。"}}',
             'marketing_content', 'marketing_content_policy_v1', '["en","zh-CN"]',
             'requested_then_tenant_default', 'available');

        INSERT INTO agent_capabilities
            (id, capability_key, display_name, description, status)
        VALUES
            ('{CAPABILITY_ID}', 'public_marketing_content_generation',
             '{{"en":"Public marketing content generation eligibility","zh-CN":"公开营销内容生成资格"}}',
             '{{"en":"Eligibility to create governed drafts only and no approval, publishing, communication, scheduling, or CRM write authority.","zh-CN":"仅授予创建受治理草稿的资格；不授予审批、发布、沟通、排期或 CRM 写入权限。"}}',
             'available');

        INSERT INTO agent_configurations
            (id, tenant_id, agent_id, agent_key, version_number, status, instructions_ref,
             input_schema_version, output_schema_version, config_digest, supported_locales,
             response_locale_policy, runtime_config)
        VALUES
            ('{CONFIG_ID}', '{TENANT_ID}', '{AGENT_ID}', 'marketing_content', 1, 'active',
             'sari_api.domain.packages.marketing_content:MARKETING_CONTENT_AGENT_PACKAGE',
             'marketing_content_request_v1', 'marketing_content_draft_v1', repeat('d', 64),
             '["en","zh-CN"]', 'requested_then_tenant_default',
             jsonb_build_object(
                'execution_enabled', false,
                'generation_enabled', false,
                'knowledge_enabled', true,
                'knowledge_policy', 'public_marketing_v1',
                'human_review_required', true,
                'external_actions_enabled', false
             ));

        INSERT INTO agent_capability_bindings
            (id, tenant_id, agent_configuration_id, capability_id, requirement_level, status,
             binding_config)
        SELECT gen_random_uuid(), '{TENANT_ID}', '{CONFIG_ID}', capability_id, 'required',
               'available', binding_config
        FROM (VALUES
            ('{CAPABILITY_ID}'::uuid,
             '{{"eligibility_only":true,"approval":false,"publishing":false,"external_communication":false,"crm_write":false}}'::jsonb),
            ('62000000-0000-4000-8000-000000000005'::uuid,
             '{{"policy":"public_marketing_v1","visibility":"public_marketing","deny_by_default":true}}'::jsonb),
            ('62000000-0000-4000-8000-000000000004'::uuid,
             '{{"required_for_generated_content":true,"agent_may_approve":false}}'::jsonb)
        ) AS bindings(capability_id, binding_config);

        INSERT INTO tenant_agent_activations
            (id, tenant_id, agent_id, agent_configuration_id, environment, status,
             locale_policy, rollout_percentage, activated_at, reason)
        VALUES
            ('{DEVELOPMENT_ACTIVATION_ID}', '{TENANT_ID}', '{AGENT_ID}', '{CONFIG_ID}',
             'development', 'active', '{{"default":"en","supported":["en","zh-CN"]}}',
             100, now(),
             'Policy-validation activation only with AI generation and external actions disabled'),
            ('{PRODUCTION_ACTIVATION_ID}', '{TENANT_ID}', '{AGENT_ID}', '{CONFIG_ID}',
             'production', 'pending', '{{"default":"en","supported":["en","zh-CN"]}}',
             0, NULL,
             'Production activation requires approved knowledge, evaluation, and explicit release approval');
        """
    )


def downgrade() -> None:
    _execute_statements(
        f"""
        DELETE FROM tenant_agent_activations
         WHERE id IN ('{DEVELOPMENT_ACTIVATION_ID}', '{PRODUCTION_ACTIVATION_ID}');
        DELETE FROM agent_capability_bindings WHERE agent_configuration_id = '{CONFIG_ID}';
        DELETE FROM agent_configurations WHERE id = '{CONFIG_ID}';
        DELETE FROM agent_capabilities WHERE id = '{CAPABILITY_ID}';
        DELETE FROM agents WHERE id = '{AGENT_ID}';
        """
    )


def _execute_statements(sql: str) -> None:
    connection = op.get_bind()
    for statement in sql.split(";"):
        if statement.strip():
            connection.exec_driver_sql(statement)
