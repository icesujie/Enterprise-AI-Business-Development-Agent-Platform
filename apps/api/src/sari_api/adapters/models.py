from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

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
    agent_key: Mapped[str] = mapped_column(String(80))
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    instructions_ref: Mapped[str] = mapped_column(String(255))
    output_schema_version: Mapped[str] = mapped_column(String(50))
    runtime_config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRun(TimestampVersionMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','awaiting_approval','succeeded','failed','cancelled')",
            name="agent_runs_status_check",
        ),
        Index("ix_agent_runs_tenant_status_created", "tenant_id", "status", "created_at"),
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
