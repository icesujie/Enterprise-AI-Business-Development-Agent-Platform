from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampVersionMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint("status IN ('active','suspended','closed')", name="tenants_status_check"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), server_default="active")
    default_locale: Mapped[str] = mapped_column(String(20), server_default="en")
    default_timezone: Mapped[str] = mapped_column(String(64), server_default="Asia/Jakarta")
    default_currency: Mapped[str] = mapped_column(String(3), server_default="IDR")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("identity_provider", "external_subject"),
        CheckConstraint("status IN ('active','disabled')", name="users_status_check"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_provider: Mapped[str] = mapped_column(String(50), server_default="supabase")
    external_subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), server_default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TenantMembership(TimestampVersionMixin, Base):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id"),
        CheckConstraint(
            "status IN ('invited','active','suspended')",
            name="tenant_memberships_status_check",
        ),
        CheckConstraint("role IN ('admin','sales')", name="tenant_memberships_role_check"),
        Index("ix_memberships_user_status", "user_id", "status"),
        Index("ix_memberships_tenant_role", "tenant_id", "role"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), server_default="active")
    job_title: Mapped[str | None] = mapped_column(String(120))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TenantMutableMixin(TimestampVersionMixin):
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Organization(TenantMutableMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_stage IN ('prospect','qualified','customer','inactive')",
            name="organizations_lifecycle_stage_check",
        ),
        Index("ix_organizations_tenant_name", "tenant_id", "display_name"),
        Index("ix_organizations_tenant_domain", "tenant_id", "domain"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    legal_name: Mapped[str] = mapped_column(String(250))
    display_name: Mapped[str] = mapped_column(String(250))
    website_url: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(120))
    country_code: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(120))
    preferred_language: Mapped[str | None] = mapped_column(String(20))
    lifecycle_stage: Mapped[str] = mapped_column(String(30), server_default="prospect")
    owner_membership_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenant_memberships.id"))


class Contact(TenantMutableMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (
        CheckConstraint(
            "first_name IS NOT NULL OR last_name IS NOT NULL "
            "OR email IS NOT NULL OR phone_e164 IS NOT NULL",
            name="contacts_check",
        ),
        Index("ix_contacts_tenant_email", "tenant_id", "email"),
        Index("ix_contacts_tenant_phone", "tenant_id", "phone_e164"),
        Index("ix_contacts_tenant_organization", "tenant_id", "organization_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    job_title: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(320))
    phone_e164: Mapped[str | None] = mapped_column(String(20))
    whatsapp_e164: Mapped[str | None] = mapped_column(String(20))
    preferred_language: Mapped[str | None] = mapped_column(String(20))
    marketing_consent_status: Mapped[str] = mapped_column(String(30), server_default="unknown")
    do_not_contact: Mapped[bool] = mapped_column(Boolean, server_default="false")
    owner_membership_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenant_memberships.id"))


class Lead(TenantMutableMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new','qualifying','qualified','nurture',"
            "'disqualified','converted','archived')",
            name="leads_status_check",
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','urgent')", name="leads_priority_check"
        ),
        CheckConstraint(
            "estimated_value IS NULL OR estimated_value >= 0",
            name="leads_estimated_value_check",
        ),
        CheckConstraint(
            "(estimated_value IS NULL AND currency IS NULL) OR "
            "(estimated_value IS NOT NULL AND currency IS NOT NULL)",
            name="leads_money_pair_check",
        ),
        CheckConstraint(
            "qualification_score IS NULL OR qualification_score BETWEEN 0 AND 100",
            name="leads_qualification_score_check",
        ),
        Index(
            "ix_leads_tenant_work_queue",
            "tenant_id",
            "status",
            "owner_membership_id",
            "priority",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id: Mapped[UUID | None] = mapped_column(ForeignKey("contacts.id"))
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    source_channel: Mapped[str] = mapped_column(String(30))
    source_detail: Mapped[str | None] = mapped_column(String(200))
    inquiry_summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), server_default="new")
    priority: Mapped[str] = mapped_column(String(20), server_default="normal")
    owner_membership_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenant_memberships.id"))
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    target_timeline: Mapped[str | None] = mapped_column(String(100))
    project_country_code: Mapped[str | None] = mapped_column(String(2))
    project_city: Mapped[str | None] = mapped_column(String(120))
    project_type: Mapped[str | None] = mapped_column(String(120))
    expected_capacity: Mapped[str | None] = mapped_column(String(120))
    requirements: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    qualification_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class Opportunity(TenantMutableMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_lead_id"),
        CheckConstraint(
            "stage IN ('discovery','requirements_confirmed','proposal','negotiation','won','lost')",
            name="opportunities_stage_check",
        ),
        CheckConstraint(
            "status IN ('open','won','lost','cancelled')",
            name="opportunities_status_check",
        ),
        CheckConstraint("probability BETWEEN 0 AND 100", name="opportunities_probability_check"),
        CheckConstraint("estimated_value >= 0", name="opportunities_estimated_value_check"),
        Index(
            "ix_opportunities_tenant_pipeline",
            "tenant_id",
            "status",
            "stage",
            "expected_close_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    primary_contact_id: Mapped[UUID | None] = mapped_column(ForeignKey("contacts.id"))
    source_lead_id: Mapped[UUID | None] = mapped_column(ForeignKey("leads.id"))
    name: Mapped[str] = mapped_column(String(250))
    stage: Mapped[str] = mapped_column(String(40), server_default="discovery")
    status: Mapped[str] = mapped_column(String(20), server_default="open")
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="10")
    estimated_value: Mapped[Decimal] = mapped_column(Numeric(19, 4), server_default="0")
    currency: Mapped[str] = mapped_column(String(3), server_default="IDR")
    expected_close_date: Mapped[date | None] = mapped_column(Date)
    requirements: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    owner_membership_id: Mapped[UUID] = mapped_column(ForeignKey("tenant_memberships.id"))


class Task(TenantMutableMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','in_progress','completed','cancelled')",
            name="tasks_status_check",
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','urgent')", name="tasks_priority_check"
        ),
        CheckConstraint(
            "lead_id IS NOT NULL OR opportunity_id IS NOT NULL OR organization_id IS NOT NULL",
            name="tasks_check",
        ),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR "
            "(status <> 'completed' AND completed_at IS NULL)",
            name="tasks_completion_check",
        ),
        Index("ix_tasks_tenant_assignee_due", "tenant_id", "assigned_to", "status", "due_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id: Mapped[UUID | None] = mapped_column(ForeignKey("leads.id"))
    opportunity_id: Mapped[UUID | None] = mapped_column(ForeignKey("opportunities.id"))
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), server_default="open")
    priority: Mapped[str] = mapped_column(String(20), server_default="normal")
    assigned_to: Mapped[UUID] = mapped_column(ForeignKey("tenant_memberships.id"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint(
            "lead_id IS NOT NULL OR opportunity_id IS NOT NULL "
            "OR organization_id IS NOT NULL OR contact_id IS NOT NULL",
            name="activities_check",
        ),
        Index("ix_activities_tenant_occurred", "tenant_id", "occurred_at"),
        Index("ix_activities_tenant_lead_occurred", "tenant_id", "lead_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    lead_id: Mapped[UUID | None] = mapped_column(ForeignKey("leads.id"))
    opportunity_id: Mapped[UUID | None] = mapped_column(ForeignKey("opportunities.id"))
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    contact_id: Mapped[UUID | None] = mapped_column(ForeignKey("contacts.id"))
    activity_type: Mapped[str] = mapped_column(String(50))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    subject: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    actor_membership_id: Mapped[UUID] = mapped_column(ForeignKey("tenant_memberships.id"))
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DomainPackage(Base):
    __tablename__ = "domain_packages"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','available','suspended','deprecated','retired')",
            name="domain_packages_status_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_key: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[dict[str, str]] = mapped_column(JSONB)
    description: Mapped[dict[str, str]] = mapped_column(JSONB, server_default="{}")
    package_key: Mapped[str] = mapped_column(String(120))
    package_version: Mapped[str] = mapped_column(String(40))
    implementation_ref: Mapped[str] = mapped_column(String(255))
    supported_locales: Mapped[list[str]] = mapped_column(JSONB)
    default_locale: Mapped[str] = mapped_column(String(20), server_default="en")
    status: Mapped[str] = mapped_column(String(30), server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','available','suspended','deprecated','retired')",
            name="agents_status_check",
        ),
        Index("ix_agents_domain_type_status", "domain_package_id", "agent_type", "status"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_package_id: Mapped[UUID] = mapped_column(ForeignKey("domain_packages.id"))
    agent_key: Mapped[str] = mapped_column(String(120), unique=True)
    display_name: Mapped[dict[str, str]] = mapped_column(JSONB)
    description: Mapped[dict[str, str]] = mapped_column(JSONB, server_default="{}")
    agent_type: Mapped[str] = mapped_column(String(60))
    implementation_key: Mapped[str] = mapped_column(String(160))
    supported_locales: Mapped[list[str]] = mapped_column(JSONB)
    response_locale_policy: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AgentCapability(Base):
    __tablename__ = "agent_capabilities"
    __table_args__ = (
        CheckConstraint(
            "status IN ('available','planned','retired')",
            name="agent_capabilities_status_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    capability_key: Mapped[str] = mapped_column(String(120), unique=True)
    display_name: Mapped[dict[str, str]] = mapped_column(JSONB)
    description: Mapped[dict[str, str]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[str] = mapped_column(String(30), server_default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentCapabilityBinding(Base):
    __tablename__ = "agent_capability_bindings"
    __table_args__ = (
        UniqueConstraint("agent_configuration_id", "capability_id"),
        CheckConstraint(
            "requirement_level IN ('required','optional')",
            name="agent_capability_bindings_requirement_check",
        ),
        CheckConstraint(
            "status IN ('available','planned','disabled')",
            name="agent_capability_bindings_status_check",
        ),
        Index(
            "ix_agent_capability_bindings_tenant_config",
            "tenant_id",
            "agent_configuration_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    agent_configuration_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_configurations.id", ondelete="CASCADE")
    )
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("agent_capabilities.id"))
    requirement_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    binding_config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TenantAgentActivation(Base):
    __tablename__ = "tenant_agent_activations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_id", "environment"),
        CheckConstraint(
            "environment IN ('development','staging','production')",
            name="tenant_agent_activations_environment_check",
        ),
        CheckConstraint(
            "status IN ('pending','active','suspended','retired')",
            name="tenant_agent_activations_status_check",
        ),
        CheckConstraint(
            "rollout_percentage BETWEEN 0 AND 100",
            name="tenant_agent_activations_rollout_check",
        ),
        Index(
            "ix_tenant_agent_activations_status",
            "tenant_id",
            "status",
            "agent_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"))
    agent_configuration_id: Mapped[UUID] = mapped_column(ForeignKey("agent_configurations.id"))
    environment: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    locale_policy: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    rollout_percentage: Mapped[int] = mapped_column(Integer, server_default="100")
    activated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_key", "version_number"),
        CheckConstraint(
            "status IN ('draft','active','retired')",
            name="agent_configurations_status_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"))
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id"))
    agent_key: Mapped[str] = mapped_column(String(80))
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    instructions_ref: Mapped[str] = mapped_column(String(255))
    input_schema_version: Mapped[str | None] = mapped_column(String(50))
    output_schema_version: Mapped[str] = mapped_column(String(50))
    config_digest: Mapped[str | None] = mapped_column(String(64))
    supported_locales: Mapped[list[str]] = mapped_column(JSONB, server_default='["en"]')
    response_locale_policy: Mapped[str] = mapped_column(
        String(80), server_default="requested_then_tenant_default"
    )
    runtime_config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeSource(TimestampVersionMixin, Base):
    __tablename__ = "knowledge_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_key"),
        CheckConstraint(
            "source_type IN ('manual_upload','approved_import')",
            name="knowledge_sources_type_check",
        ),
        CheckConstraint(
            "status IN ('active','disabled')",
            name="knowledge_sources_status_check",
        ),
        Index("ix_knowledge_sources_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    source_key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(30), server_default="manual_upload")
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class KnowledgeBinding(Base):
    __tablename__ = "knowledge_bindings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_id", "domain_package_id", "agent_id"),
        CheckConstraint(
            "status IN ('enabled','disabled')",
            name="knowledge_bindings_status_check",
        ),
        Index(
            "ix_knowledge_bindings_access",
            "tenant_id",
            "agent_id",
            "domain_package_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_sources.id", ondelete="CASCADE"))
    domain_package_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    knowledge_category: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), server_default="disabled")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeDocument(TimestampVersionMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_id", "content_sha256"),
        UniqueConstraint("tenant_id", "object_key"),
        CheckConstraint(
            "approval_status IN ('pending','approved','rejected','retired')",
            name="knowledge_documents_approval_check",
        ),
        CheckConstraint(
            "ingestion_status IN ('not_started','queued','processing','ready','failed')",
            name="knowledge_documents_ingestion_check",
        ),
        CheckConstraint("byte_size > 0", name="knowledge_documents_size_check"),
        Index(
            "ix_knowledge_documents_tenant_source_status",
            "tenant_id",
            "source_id",
            "approval_status",
            "ingestion_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_sources.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(300))
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(20), server_default="en")
    object_key: Mapped[str] = mapped_column(String(500))
    content_sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    approval_status: Mapped[str] = mapped_column(String(20), server_default="pending")
    ingestion_status: Mapped[str] = mapped_column(String(20), server_default="not_started")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class KnowledgeIngestionRun(Base):
    __tablename__ = "knowledge_ingestion_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','processing','succeeded','failed')",
            name="knowledge_ingestion_runs_status_check",
        ),
        Index("ix_knowledge_ingestion_runs_tenant_status", "tenant_id", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(20), server_default="queued")
    extraction_version: Mapped[str] = mapped_column(String(40), server_default="extract_v1")
    chunking_version: Mapped[str] = mapped_column(String(40), server_default="chunk_v1")
    embedding_provider: Mapped[str] = mapped_column(String(80))
    embedding_model: Mapped[str] = mapped_column(String(120))
    chunk_count: Mapped[int] = mapped_column(Integer, server_default="0")
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message_safe: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", "chunk_index"),
        Index("ix_knowledge_chunks_tenant_document", "tenant_id", "document_id", "chunk_index"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_sources.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE")
    )
    ingestion_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_ingestion_runs.id", ondelete="RESTRICT")
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    character_count: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(300))
    citation_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    embedding: Mapped[list[float]] = mapped_column(VECTOR(1536))
    embedding_provider: Mapped[str] = mapped_column(String(80))
    embedding_model: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeCollection(TimestampVersionMixin, Base):
    __tablename__ = "knowledge_collections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "collection_key"),
        CheckConstraint(
            "status IN ('active','archived')", name="knowledge_collections_status_check"
        ),
        Index(
            "ix_knowledge_collections_tenant_domain",
            "tenant_id",
            "domain_package_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    domain_package_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    collection_key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    collection_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class ManagedKnowledgeDocument(TimestampVersionMixin, Base):
    __tablename__ = "managed_knowledge_documents"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN "
            "('draft','uploaded','processing','review','approved','published','active','archived')",
            name="managed_knowledge_documents_lifecycle_check",
        ),
        CheckConstraint(
            "approval_status IN ('pending','approved','rejected')",
            name="managed_knowledge_documents_approval_check",
        ),
        CheckConstraint(
            "processing_status IN ('uploaded','processing','completed','failed')",
            name="managed_knowledge_documents_processing_check",
        ),
        CheckConstraint(
            "current_version_number > 0", name="managed_knowledge_documents_version_check"
        ),
        Index(
            "ix_managed_knowledge_documents_tenant_collection",
            "tenant_id",
            "collection_id",
            "lifecycle_status",
        ),
        Index(
            "ix_managed_knowledge_documents_tenant_search",
            "tenant_id",
            "domain_package_id",
            "agent_id",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    domain_package_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_collections.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(300))
    document_type: Mapped[str] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(20), server_default="en")
    lifecycle_status: Mapped[str] = mapped_column(String(20), server_default="draft")
    approval_status: Mapped[str] = mapped_column(String(20), server_default="pending")
    processing_status: Mapped[str] = mapped_column(String(20), server_default="uploaded")
    current_version_number: Mapped[int] = mapped_column(Integer, server_default="1")
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    published_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    active_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    document_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archive_reason: Mapped[str | None] = mapped_column(Text)
    restore_reason: Mapped[str | None] = mapped_column(Text)


class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", "version_number"),
        UniqueConstraint("tenant_id", "object_key"),
        CheckConstraint("byte_size > 0", name="knowledge_document_versions_size_check"),
        CheckConstraint(
            "status IN "
            "('draft','uploaded','processing','review','approved','published','active',"
            "'archived','rejected','superseded')",
            name="knowledge_document_versions_status_check",
        ),
        CheckConstraint(
            "review_status IN ('pending','approved','rejected')",
            name="knowledge_document_versions_review_check",
        ),
        CheckConstraint(
            "created_from_action IN ('upload','rollback')",
            name="knowledge_document_versions_origin_check",
        ),
        Index(
            "ix_knowledge_document_versions_tenant_document",
            "tenant_id",
            "document_id",
            "version_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column(Integer)
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(120))
    object_key: Mapped[str] = mapped_column(String(500))
    content_sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    version_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[str] = mapped_column(String(20), server_default="uploaded")
    review_status: Mapped[str] = mapped_column(String(20), server_default="pending")
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    restored_from_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT")
    )
    created_from_action: Mapped[str] = mapped_column(String(30), server_default="upload")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeAuditLog(Base):
    __tablename__ = "knowledge_audit_logs"
    __table_args__ = (
        Index(
            "ix_knowledge_audit_logs_tenant_document",
            "tenant_id",
            "document_id",
            "created_at",
        ),
        Index(
            "ix_knowledge_audit_logs_tenant_version",
            "tenant_id",
            "document_version_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("managed_knowledge_documents.id", ondelete="RESTRICT")
    )
    document_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT")
    )
    actor_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(80))
    before_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    after_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeDocumentAgentBinding(Base):
    __tablename__ = "knowledge_document_agent_bindings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", "agent_id"),
        CheckConstraint(
            "status IN ('enabled','disabled')",
            name="knowledge_document_agent_bindings_status_check",
        ),
        Index(
            "ix_knowledge_document_agent_bindings_access",
            "tenant_id",
            "agent_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE")
    )
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), server_default="enabled")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeProcessingRun(Base):
    __tablename__ = "knowledge_processing_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('uploaded','processing','completed','failed')",
            name="knowledge_processing_runs_status_check",
        ),
        CheckConstraint(
            "chunk_size > 0 AND chunk_overlap >= 0 AND chunk_overlap < chunk_size",
            name="knowledge_processing_runs_chunking_check",
        ),
        CheckConstraint(
            "embedding_dimensions = 1536",
            name="knowledge_processing_runs_dimensions_check",
        ),
        Index(
            "ix_knowledge_processing_runs_tenant_document",
            "tenant_id",
            "document_id",
            "created_at",
        ),
        Index(
            "ix_knowledge_processing_runs_tenant_status",
            "tenant_id",
            "status",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE")
    )
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(20), server_default="uploaded")
    extractor_version: Mapped[str] = mapped_column(String(40), server_default="extract_v2")
    chunking_version: Mapped[str] = mapped_column(String(40), server_default="chunk_v1")
    chunk_size: Mapped[int] = mapped_column(Integer)
    chunk_overlap: Mapped[int] = mapped_column(Integer)
    embedding_provider: Mapped[str] = mapped_column(String(80))
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding_dimensions: Mapped[int] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer, server_default="0")
    source_metadata_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message_safe: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ManagedKnowledgeChunk(Base):
    __tablename__ = "managed_knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_version_id", "agent_id", "chunk_index"),
        Index(
            "ix_managed_knowledge_chunks_access",
            "tenant_id",
            "domain_package_id",
            "agent_id",
            "document_id",
        ),
        Index(
            "ix_managed_knowledge_chunks_version",
            "tenant_id",
            "document_version_id",
            "chunk_index",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    domain_package_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_collections.id", ondelete="RESTRICT")
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("managed_knowledge_documents.id", ondelete="CASCADE")
    )
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_document_versions.id", ondelete="CASCADE")
    )
    processing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_processing_runs.id", ondelete="RESTRICT")
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    character_count: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(String(300))
    language: Mapped[str] = mapped_column(String(20))
    document_type: Mapped[str] = mapped_column(String(80))
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    citation_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    embedding: Mapped[list[float]] = mapped_column(VECTOR(1536))
    embedding_provider: Mapped[str] = mapped_column(String(80))
    embedding_model: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentRequest(Base):
    __tablename__ = "content_requests"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('website_article','case_study','tiktok_script',"
            "'instagram_reel_script','facebook_post','email_draft')",
            name="content_requests_type_check",
        ),
        CheckConstraint(
            "audience IN ('schools','hospitals','factories','central_kitchens',"
            "'project_owners','facility_managers')",
            name="content_requests_audience_check",
        ),
        CheckConstraint("language IN ('en','zh-CN')", name="content_requests_language_check"),
        CheckConstraint(
            "channel IN ('website','tiktok','instagram','facebook','email')",
            name="content_requests_channel_check",
        ),
        CheckConstraint(
            "status IN ('draft','queued','running','completed','insufficient_evidence',"
            "'failed','cancelled','archived')",
            name="content_requests_status_check",
        ),
        Index("ix_content_requests_tenant_status", "tenant_id", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    domain_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    requested_by: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    content_type: Mapped[str] = mapped_column(String(40))
    audience: Mapped[str] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(30))
    business_objective: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(Text)
    call_to_action: Mapped[str] = mapped_column(Text)
    campaign_name: Mapped[str | None] = mapped_column(String(200))
    constraints: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    knowledge_collection_ids: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    status: Mapped[str] = mapped_column(String(30), server_default="draft")
    result_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_assets.id", ondelete="RESTRICT", use_alter=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ContentAsset(Base):
    __tablename__ = "content_assets"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('website_article','case_study','tiktok_script',"
            "'instagram_reel_script','facebook_post','email_draft')",
            name="content_assets_type_check",
        ),
        CheckConstraint(
            "audience IN ('schools','hospitals','factories','central_kitchens',"
            "'project_owners','facility_managers')",
            name="content_assets_audience_check",
        ),
        CheckConstraint("language IN ('en','zh-CN')", name="content_assets_language_check"),
        CheckConstraint(
            "channel IN ('website','tiktok','instagram','facebook','email')",
            name="content_assets_channel_check",
        ),
        CheckConstraint(
            "status IN ('draft','generated','review','approved','archived')",
            name="content_assets_status_check",
        ),
        CheckConstraint("record_version > 0", name="content_assets_record_version_check"),
        Index("ix_content_assets_tenant_status", "tenant_id", "status", "updated_at"),
        Index("ix_content_assets_tenant_owner", "tenant_id", "owner_membership_id", "status"),
        Index(
            "ix_content_assets_tenant_classification",
            "tenant_id",
            "content_type",
            "language",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    domain_id: Mapped[UUID] = mapped_column(
        ForeignKey("domain_packages.id", ondelete="RESTRICT")
    )
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_requests.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(250))
    content_type: Mapped[str] = mapped_column(String(40))
    audience: Mapped[str] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    owner_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    creator_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    approved_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    record_version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    archive_reason: Mapped[str | None] = mapped_column(Text)


class ContentGenerationRun(Base):
    __tablename__ = "content_generation_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_run_id"),
        CheckConstraint(
            "evidence_status IS NULL OR evidence_status IN "
            "('sufficient','insufficient','conflicting')",
            name="content_generation_runs_evidence_check",
        ),
        Index(
            "ix_content_generation_runs_tenant_request",
            "tenant_id",
            "content_request_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    content_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_requests.id", ondelete="RESTRICT")
    )
    agent_run_id: Mapped[UUID] = mapped_column(ForeignKey("agent_runs.id", ondelete="RESTRICT"))
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"))
    agent_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_configurations.id", ondelete="RESTRICT")
    )
    provider: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    evidence_status: Mapped[str | None] = mapped_column(String(20))
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    output_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT", use_alter=True)
    )
    validation_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    token_usage: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(19, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContentVersion(Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "content_asset_id", "version_number"),
        CheckConstraint("version_number > 0", name="content_versions_number_check"),
        CheckConstraint(
            "origin IN ('human','ai_generated','rollback')",
            name="content_versions_origin_check",
        ),
        CheckConstraint("length(content_sha256) = 64", name="content_versions_sha_check"),
        Index(
            "ix_content_versions_tenant_asset",
            "tenant_id",
            "content_asset_id",
            "version_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    content_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_assets.id", ondelete="RESTRICT")
    )
    version_number: Mapped[int] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(String(20))
    content_body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    plain_text: Mapped[str] = mapped_column(Text)
    claims: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default="[]")
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default="[]")
    generation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_generation_runs.id", ondelete="RESTRICT")
    )
    based_on_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT")
    )
    content_sha256: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentApprovalDecision(Base):
    __tablename__ = "content_approval_decisions"
    __table_args__ = (
        CheckConstraint(
            "decision_type IN ('submitted','changes_requested','approved','rejected')",
            name="content_approval_decisions_type_check",
        ),
        CheckConstraint(
            "length(content_sha256) = 64", name="content_approval_decisions_sha_check"
        ),
        Index(
            "ix_content_approval_decisions_tenant_asset",
            "tenant_id",
            "content_asset_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    content_asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_assets.id", ondelete="RESTRICT")
    )
    content_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT")
    )
    decision_type: Mapped[str] = mapped_column(String(30))
    decided_by: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    content_sha256: Mapped[str] = mapped_column(String(64))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentAuditLog(Base):
    __tablename__ = "content_audit_logs"
    __table_args__ = (
        Index(
            "ix_content_audit_logs_tenant_asset",
            "tenant_id",
            "content_asset_id",
            "created_at",
        ),
        Index(
            "ix_content_audit_logs_tenant_request",
            "tenant_id",
            "content_request_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    actor_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    content_asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_assets.id", ondelete="RESTRICT")
    )
    content_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_versions.id", ondelete="RESTRICT")
    )
    content_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_requests.id", ondelete="RESTRICT")
    )
    content_generation_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_generation_runs.id", ondelete="RESTRICT")
    )
    outcome: Mapped[str] = mapped_column(String(30), server_default="success")
    before_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    after_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRun(TimestampVersionMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','awaiting_approval','succeeded','failed','cancelled')",
            name="agent_runs_status_check",
        ),
        Index("ix_agent_runs_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("ix_agent_runs_tenant_retry", "tenant_id", "status", "next_retry_at"),
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= max_attempts",
            name="agent_runs_attempt_count_check",
        ),
        CheckConstraint(
            "max_attempts BETWEEN 1 AND 5",
            name="agent_runs_max_attempts_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"))
    agent_configuration_id: Mapped[UUID] = mapped_column(ForeignKey("agent_configurations.id"))
    workflow_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), server_default="queued")
    initiated_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    lead_id: Mapped[UUID | None] = mapped_column(ForeignKey("leads.id"))
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    output_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    provider_type: Mapped[str | None] = mapped_column(String(120))
    model_id: Mapped[str | None] = mapped_column(String(120))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message_safe: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    attempt_count: Mapped[int] = mapped_column(Integer, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, server_default="3")
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadAssessment(Base):
    __tablename__ = "lead_assessments"
    __table_args__ = (
        UniqueConstraint("lead_id", "assessment_version"),
        CheckConstraint("score BETWEEN 0 AND 100", name="lead_assessments_score_check"),
        CheckConstraint("tier IN ('hot','warm','cold')", name="lead_assessments_tier_check"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="lead_assessments_confidence_check"),
        CheckConstraint(
            "review_status IN ('not_required','pending','approved','rejected','superseded')",
            name="lead_assessments_review_status_check",
        ),
        Index("ix_assessments_tenant_review", "tenant_id", "review_status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"))
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id"))
    assessment_version: Mapped[int] = mapped_column(Integer)
    agent_run_id: Mapped[UUID | None] = mapped_column(ForeignKey("agent_runs.id"))
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tier: Mapped[str] = mapped_column(String(20))
    need_summary: Mapped[str | None] = mapped_column(Text)
    qualification: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    recommended_action: Mapped[str] = mapped_column(Text)
    missing_information: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    review_status: Mapped[str] = mapped_column(String(30), server_default="pending")
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IvcQualificationAssessment(Base):
    __tablename__ = "ivc_qualification_assessments"
    __table_args__ = (
        UniqueConstraint("agent_run_id"),
        CheckConstraint(
            "score BETWEEN 0 AND 100",
            name="ivc_qualification_assessments_score_check",
        ),
        CheckConstraint(
            "qualification_level IN ('A','B','C')",
            name="ivc_qualification_assessments_level_check",
        ),
        CheckConstraint(
            "response_locale IN ('en','zh-CN','id')",
            name="ivc_qualification_assessments_locale_check",
        ),
        CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name="ivc_qualification_assessments_confidence_check",
        ),
        CheckConstraint(
            "review_status IN ('pending','approved','rejected')",
            name="ivc_qualification_assessments_review_status_check",
        ),
        Index(
            "ix_ivc_assessments_tenant_review_created",
            "tenant_id",
            "review_status",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"))
    agent_run_id: Mapped[UUID] = mapped_column(ForeignKey("agent_runs.id", ondelete="RESTRICT"))
    response_locale: Mapped[str] = mapped_column(String(20))
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    qualification_level: Mapped[str] = mapped_column(String(1))
    business_summary: Mapped[str] = mapped_column(Text)
    key_qualification_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    recommended_next_actions: Mapped[list[str]] = mapped_column(JSONB)
    missing_information: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    risk_flags: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    expert_review_required: Mapped[bool] = mapped_column(Boolean, server_default="true")
    review_status: Mapped[str] = mapped_column(String(30), server_default="pending")
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id"))
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    result: Mapped[str] = mapped_column(String(30))
    request_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("scope", "idempotency_key"),
        Index("ix_idempotency_expires", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id"))
    scope: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
