# ruff: noqa: E501 -- seed SQL contains indivisible multilingual JSON values.

"""Add the Phase 2 Agent Registry MVP.

Revision ID: 8c91f2a4d6e3
Revises: bd41a8f07c22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8c91f2a4d6e3"
down_revision: str | None = "bd41a8f07c22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_ID = "10000000-0000-4000-8000-000000000001"
SARI_CONFIG_ID = "50000000-0000-4000-8000-000000000001"
IVC_CONFIG_ID = "50000000-0000-4000-8000-000000000002"
SARI_DOMAIN_ID = "60000000-0000-4000-8000-000000000001"
IVC_DOMAIN_ID = "60000000-0000-4000-8000-000000000002"
SARI_AGENT_ID = "61000000-0000-4000-8000-000000000001"
IVC_AGENT_ID = "61000000-0000-4000-8000-000000000002"


def upgrade() -> None:
    op.create_table(
        "domain_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("domain_key", sa.String(100), nullable=False, unique=True),
        sa.Column("display_name", postgresql.JSONB(), nullable=False),
        sa.Column("description", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("package_key", sa.String(120), nullable=False),
        sa.Column("package_version", sa.String(40), nullable=False),
        sa.Column("implementation_ref", sa.String(255), nullable=False),
        sa.Column("supported_locales", postgresql.JSONB(), nullable=False),
        sa.Column("default_locale", sa.String(20), nullable=False, server_default="en"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('draft','available','suspended','deprecated','retired')",
            name="domain_packages_status_check",
        ),
    )
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "domain_package_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domain_packages.id"),
            nullable=False,
        ),
        sa.Column("agent_key", sa.String(120), nullable=False, unique=True),
        sa.Column("display_name", postgresql.JSONB(), nullable=False),
        sa.Column("description", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("agent_type", sa.String(60), nullable=False),
        sa.Column("implementation_key", sa.String(160), nullable=False),
        sa.Column("supported_locales", postgresql.JSONB(), nullable=False),
        sa.Column("response_locale_policy", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('draft','available','suspended','deprecated','retired')",
            name="agents_status_check",
        ),
    )
    op.create_index(
        "ix_agents_domain_type_status",
        "agents",
        ["domain_package_id", "agent_type", "status"],
    )
    op.create_table(
        "agent_capabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("capability_key", sa.String(120), nullable=False, unique=True),
        sa.Column("display_name", postgresql.JSONB(), nullable=False),
        sa.Column("description", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('available','planned','retired')",
            name="agent_capabilities_status_check",
        ),
    )

    op.add_column(
        "agent_configurations",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_agent_configurations_agent_id",
        "agent_configurations",
        "agents",
        ["agent_id"],
        ["id"],
    )
    op.add_column("agent_configurations", sa.Column("input_schema_version", sa.String(50)))
    op.add_column("agent_configurations", sa.Column("config_digest", sa.String(64)))
    op.add_column(
        "agent_configurations",
        sa.Column(
            "supported_locales",
            postgresql.JSONB(),
            nullable=False,
            server_default='["en"]',
        ),
    )
    op.add_column(
        "agent_configurations",
        sa.Column(
            "response_locale_policy",
            sa.String(80),
            nullable=False,
            server_default="requested_then_tenant_default",
        ),
    )

    op.create_table(
        "agent_capability_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False
        ),
        sa.Column(
            "agent_configuration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_configurations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "capability_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_capabilities.id"),
            nullable=False,
        ),
        sa.Column("requirement_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("binding_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("agent_configuration_id", "capability_id"),
        sa.CheckConstraint(
            "requirement_level IN ('required','optional')",
            name="agent_capability_bindings_requirement_check",
        ),
        sa.CheckConstraint(
            "status IN ('available','planned','disabled')",
            name="agent_capability_bindings_status_check",
        ),
    )
    op.create_index(
        "ix_agent_capability_bindings_tenant_config",
        "agent_capability_bindings",
        ["tenant_id", "agent_configuration_id", "status"],
    )
    op.create_table(
        "tenant_agent_activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False
        ),
        sa.Column(
            "agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False
        ),
        sa.Column(
            "agent_configuration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_configurations.id"),
            nullable=False,
        ),
        sa.Column("environment", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("locale_policy", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("activated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("suspended_at", sa.DateTime(timezone=True)),
        sa.Column("reason", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "agent_id", "environment"),
        sa.CheckConstraint(
            "environment IN ('development','staging','production')",
            name="tenant_agent_activations_environment_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending','active','suspended','retired')",
            name="tenant_agent_activations_status_check",
        ),
        sa.CheckConstraint(
            "rollout_percentage BETWEEN 0 AND 100",
            name="tenant_agent_activations_rollout_check",
        ),
    )
    op.create_index(
        "ix_tenant_agent_activations_status",
        "tenant_agent_activations",
        ["tenant_id", "status", "agent_id"],
    )

    tenant_expression = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    for table_name in ("agent_capability_bindings", "tenant_agent_activations"):
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY tenant_isolation ON "{table_name}" '
                f"USING ({tenant_expression}) WITH CHECK ({tenant_expression})"
            )
        )

    _seed_registry()


def _seed_registry() -> None:
    seed_sql = f"""
            INSERT INTO domain_packages
                (id, domain_key, display_name, description, package_key, package_version,
                 implementation_ref, supported_locales, default_locale, status)
            VALUES
                ('{SARI_DOMAIN_ID}', 'commercial_kitchen',
                 '{{"en":"Commercial Kitchen","zh-CN":"商用厨房","id":"Dapur Komersial"}}',
                 '{{"en":"Commercial kitchen engineering and project delivery.","zh-CN":"商用厨房工程与项目交付。","id":"Rekayasa dan pelaksanaan proyek dapur komersial."}}',
                 'commercial_kitchen', '1.0.0',
                 'sari_api.domain.packages.commercial_kitchen:COMMERCIAL_KITCHEN_PACKAGE',
                 '["en","zh-CN","id"]', 'en', 'available'),
                ('{IVC_DOMAIN_ID}', 'laboratory_animal_facility',
                 '{{"en":"Laboratory Animal Facility","zh-CN":"实验动物设施","id":"Fasilitas Hewan Laboratorium"}}',
                 '{{"en":"IVC and laboratory animal facility business development.","zh-CN":"IVC 与实验动物设施商务拓展。","id":"Pengembangan bisnis IVC dan fasilitas hewan laboratorium."}}',
                 'laboratory_animal_facility', '1.0.0',
                 'sari_api.domain.packages.laboratory_animal_facility:LABORATORY_ANIMAL_FACILITY_PACKAGE',
                 '["en","zh-CN","id"]', 'en', 'draft');

            INSERT INTO agents
                (id, domain_package_id, agent_key, display_name, description, agent_type,
                 implementation_key, supported_locales, response_locale_policy, status)
            VALUES
                ('{SARI_AGENT_ID}', '{SARI_DOMAIN_ID}', 'commercial_kitchen.lead_qualification',
                 '{{"en":"Sari Arta Commercial Kitchen Agent","zh-CN":"Sari Arta 商用厨房智能体","id":"Agen Dapur Komersial Sari Arta"}}',
                 '{{"en":"Qualifies commercial kitchen opportunities.","zh-CN":"评估商用厨房项目机会。","id":"Mengkualifikasi peluang proyek dapur komersial."}}',
                 'business_development', 'lead_qualification_v1', '["en","zh-CN","id"]',
                 'requested_then_tenant_default', 'available'),
                ('{IVC_AGENT_ID}', '{IVC_DOMAIN_ID}', 'laboratory_animal_facility.ivc_business_development',
                 '{{"en":"IVC Facility Business Development Agent","zh-CN":"IVC 设施商务拓展智能体","id":"Agen Pengembangan Bisnis Fasilitas IVC"}}',
                 '{{"en":"Qualifies IVC and laboratory animal facility opportunities.","zh-CN":"评估 IVC 与实验动物设施项目机会。","id":"Mengkualifikasi peluang IVC dan fasilitas hewan laboratorium."}}',
                 'business_development', 'ivc_business_development_v1', '["en","zh-CN","id"]',
                 'requested_then_tenant_default', 'draft');

            INSERT INTO agent_capabilities (id, capability_key, display_name, description, status)
            VALUES
                ('62000000-0000-4000-8000-000000000001', 'lead_qualification',
                 '{{"en":"Lead qualification","zh-CN":"线索资格评估","id":"Kualifikasi prospek"}}', '{{}}', 'available'),
                ('62000000-0000-4000-8000-000000000002', 'structured_output',
                 '{{"en":"Structured output","zh-CN":"结构化输出","id":"Keluaran terstruktur"}}', '{{}}', 'available'),
                ('62000000-0000-4000-8000-000000000003', 'localized_response',
                 '{{"en":"Localized response","zh-CN":"本地化响应","id":"Respons terlokalisasi"}}', '{{}}', 'available'),
                ('62000000-0000-4000-8000-000000000004', 'human_review',
                 '{{"en":"Human review","zh-CN":"人工审核","id":"Tinjauan manusia"}}', '{{}}', 'available'),
                ('62000000-0000-4000-8000-000000000005', 'approved_knowledge_retrieval',
                 '{{"en":"Approved knowledge retrieval","zh-CN":"批准知识检索","id":"Pengambilan pengetahuan disetujui"}}', '{{}}', 'planned');

            UPDATE agent_configurations SET
                agent_id = '{SARI_AGENT_ID}',
                input_schema_version = 'lead_qualification_input_v1',
                config_digest = repeat('a', 64),
                supported_locales = '["en","zh-CN","id"]',
                response_locale_policy = 'requested_then_tenant_default'
            WHERE id = '{SARI_CONFIG_ID}';

            INSERT INTO agent_configurations
                (id, tenant_id, agent_id, agent_key, version_number, status, instructions_ref,
                 input_schema_version, output_schema_version, config_digest, supported_locales,
                 response_locale_policy, runtime_config)
            VALUES
                ('{IVC_CONFIG_ID}', '{TENANT_ID}', '{IVC_AGENT_ID}', 'ivc_business_development', 1,
                 'draft', 'sari_api.domain.packages.laboratory_animal_facility:LABORATORY_ANIMAL_FACILITY_PACKAGE',
                 'ivc_qualification_input_v1', 'ivc_qualification_output_v1', repeat('b', 64),
                 '["en","zh-CN","id"]', 'requested_then_tenant_default',
                 '{{"knowledge_enabled":false,"execution_enabled":false}}');

            INSERT INTO agent_capability_bindings
                (id, tenant_id, agent_configuration_id, capability_id, requirement_level, status)
            SELECT gen_random_uuid(), '{TENANT_ID}', config_id, capability_id, requirement_level, binding_status
            FROM (VALUES
                ('{SARI_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000001'::uuid, 'required', 'available'),
                ('{SARI_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000002'::uuid, 'required', 'available'),
                ('{SARI_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000003'::uuid, 'required', 'available'),
                ('{SARI_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000004'::uuid, 'required', 'available'),
                ('{SARI_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000005'::uuid, 'optional', 'planned'),
                ('{IVC_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000001'::uuid, 'required', 'available'),
                ('{IVC_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000002'::uuid, 'required', 'available'),
                ('{IVC_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000003'::uuid, 'required', 'available'),
                ('{IVC_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000004'::uuid, 'required', 'available'),
                ('{IVC_CONFIG_ID}'::uuid, '62000000-0000-4000-8000-000000000005'::uuid, 'required', 'planned')
            ) AS bindings(config_id, capability_id, requirement_level, binding_status);

            INSERT INTO tenant_agent_activations
                (id, tenant_id, agent_id, agent_configuration_id, environment, status,
                 locale_policy, rollout_percentage, activated_at, reason)
            VALUES
                ('63000000-0000-4000-8000-000000000001', '{TENANT_ID}', '{SARI_AGENT_ID}',
                 '{SARI_CONFIG_ID}', 'development', 'active',
                 '{{"default":"en","supported":["en","zh-CN","id"]}}', 100, now(),
                 'Existing Phase 1 agent registered without changing its runtime lookup');
            """
    connection = op.get_bind()
    for statement in seed_sql.split(";"):
        if statement.strip():
            connection.exec_driver_sql(statement)


def downgrade() -> None:
    op.execute(
        sa.text(
            f"""
            DELETE FROM tenant_agent_activations WHERE id = '63000000-0000-4000-8000-000000000001';
            DELETE FROM agent_capability_bindings
             WHERE agent_configuration_id IN ('{SARI_CONFIG_ID}', '{IVC_CONFIG_ID}');
            DELETE FROM agent_configurations WHERE id = '{IVC_CONFIG_ID}';
            UPDATE agent_configurations SET agent_id = NULL WHERE id = '{SARI_CONFIG_ID}';
            DELETE FROM agent_capabilities WHERE id::text LIKE '62000000-0000-4000-8000-%';
            DELETE FROM agents WHERE id IN ('{SARI_AGENT_ID}', '{IVC_AGENT_ID}');
            DELETE FROM domain_packages WHERE id IN ('{SARI_DOMAIN_ID}', '{IVC_DOMAIN_ID}');
            """
        )
    )
    for table_name in ("tenant_agent_activations", "agent_capability_bindings"):
        op.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table_name}"'))
    op.drop_index("ix_tenant_agent_activations_status", table_name="tenant_agent_activations")
    op.drop_table("tenant_agent_activations")
    op.drop_index(
        "ix_agent_capability_bindings_tenant_config",
        table_name="agent_capability_bindings",
    )
    op.drop_table("agent_capability_bindings")
    op.drop_column("agent_configurations", "response_locale_policy")
    op.drop_column("agent_configurations", "supported_locales")
    op.drop_column("agent_configurations", "config_digest")
    op.drop_column("agent_configurations", "input_schema_version")
    op.drop_constraint(
        "fk_agent_configurations_agent_id",
        "agent_configurations",
        type_="foreignkey",
    )
    op.drop_column("agent_configurations", "agent_id")
    op.drop_table("agent_capabilities")
    op.drop_index("ix_agents_domain_type_status", table_name="agents")
    op.drop_table("agents")
    op.drop_table("domain_packages")
