from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text

from sari_api.adapters.database import dispose_database, session_factory
from sari_api.adapters.models import (
    Activity,
    AgentRun,
    Contact,
    Lead,
    LeadAssessment,
    Opportunity,
    Organization,
    Task,
)

TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
ADMIN_USER_ID = UUID("20000000-0000-4000-8000-000000000001")
ADMIN_MEMBERSHIP_ID = UUID("40000000-0000-4000-8000-000000000001")
SALES_MEMBERSHIP_ID = UUID("40000000-0000-4000-8000-000000000002")
AGENT_CONFIGURATION_ID = UUID("50000000-0000-4000-8000-000000000001")

SCHOOL_ORGANIZATION_ID = UUID("d7000000-0000-4000-8000-000000000001")
HOSPITAL_ORGANIZATION_ID = UUID("d7000000-0000-4000-8000-000000000002")
FACTORY_ORGANIZATION_ID = UUID("d7000000-0000-4000-8000-000000000003")
CENTRAL_KITCHEN_ORGANIZATION_ID = UUID("d7000000-0000-4000-8000-000000000004")

SCHOOL_CONTACT_ID = UUID("d7100000-0000-4000-8000-000000000001")
HOSPITAL_CONTACT_ID = UUID("d7100000-0000-4000-8000-000000000002")
FACTORY_CONTACT_ID = UUID("d7100000-0000-4000-8000-000000000003")
CENTRAL_KITCHEN_CONTACT_ID = UUID("d7100000-0000-4000-8000-000000000004")

SCHOOL_LEAD_ID = UUID("d7200000-0000-4000-8000-000000000001")
HOSPITAL_LEAD_ID = UUID("d7200000-0000-4000-8000-000000000002")
FACTORY_LEAD_ID = UUID("d7200000-0000-4000-8000-000000000003")
CENTRAL_KITCHEN_LEAD_ID = UUID("d7200000-0000-4000-8000-000000000004")


async def seed_demo_data() -> bool:
    now = datetime.now(UTC)
    async with session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(TENANT_ID)},
        )
        marker = await session.scalar(
            select(Organization.id).where(Organization.id == SCHOOL_ORGANIZATION_ID)
        )
        if marker is not None:
            return False

        organizations = [
            Organization(
                id=SCHOOL_ORGANIZATION_ID,
                tenant_id=TENANT_ID,
                legal_name="Demo Nusantara Learning Foundation",
                display_name="Demo Nusantara Learning Foundation",
                website_url="https://nusantara-learning.example",
                domain="nusantara-learning.example",
                industry="Education",
                country_code="ID",
                city="Bandung",
                preferred_language="en",
                lifecycle_stage="qualified",
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Organization(
                id=HOSPITAL_ORGANIZATION_ID,
                tenant_id=TENANT_ID,
                legal_name="Demo Meridian Health Campus",
                display_name="Demo Meridian Health Campus",
                website_url="https://meridian-health.example",
                domain="meridian-health.example",
                industry="Healthcare",
                country_code="ID",
                city="Surabaya",
                preferred_language="en",
                lifecycle_stage="prospect",
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Organization(
                id=FACTORY_ORGANIZATION_ID,
                tenant_id=TENANT_ID,
                legal_name="Demo Garuda Components Manufacturing",
                display_name="Demo Garuda Components Manufacturing",
                website_url="https://garuda-components.example",
                domain="garuda-components.example",
                industry="Manufacturing",
                country_code="ID",
                city="Bekasi",
                preferred_language="en",
                lifecycle_stage="prospect",
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Organization(
                id=CENTRAL_KITCHEN_ORGANIZATION_ID,
                tenant_id=TENANT_ID,
                legal_name="Demo Archipelago Food Services",
                display_name="Demo Archipelago Food Services",
                website_url="https://archipelago-food.example",
                domain="archipelago-food.example",
                industry="Food service",
                country_code="ID",
                city="Jakarta",
                preferred_language="en",
                lifecycle_stage="qualified",
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
        ]
        contacts = [
            Contact(
                id=SCHOOL_CONTACT_ID,
                tenant_id=TENANT_ID,
                organization_id=SCHOOL_ORGANIZATION_ID,
                first_name="Alya",
                last_name="Pranoto",
                job_title="Campus Development Manager",
                email="alya.pranoto@nusantara-learning.example",
                preferred_language="en",
                marketing_consent_status="unknown",
                do_not_contact=False,
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Contact(
                id=HOSPITAL_CONTACT_ID,
                tenant_id=TENANT_ID,
                organization_id=HOSPITAL_ORGANIZATION_ID,
                first_name="Rafi",
                last_name="Santoso",
                job_title="Facilities Project Coordinator",
                email="rafi.santoso@meridian-health.example",
                preferred_language="en",
                marketing_consent_status="unknown",
                do_not_contact=False,
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Contact(
                id=FACTORY_CONTACT_ID,
                tenant_id=TENANT_ID,
                organization_id=FACTORY_ORGANIZATION_ID,
                first_name="Maya",
                last_name="Wijaya",
                job_title="Procurement Specialist",
                email="maya.wijaya@garuda-components.example",
                preferred_language="en",
                marketing_consent_status="unknown",
                do_not_contact=False,
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
            Contact(
                id=CENTRAL_KITCHEN_CONTACT_ID,
                tenant_id=TENANT_ID,
                organization_id=CENTRAL_KITCHEN_ORGANIZATION_ID,
                first_name="Dimas",
                last_name="Hartono",
                job_title="Operations Director",
                email="dimas.hartono@archipelago-food.example",
                preferred_language="en",
                marketing_consent_status="unknown",
                do_not_contact=False,
                owner_membership_id=SALES_MEMBERSHIP_ID,
            ),
        ]
        leads = [
            Lead(
                id=SCHOOL_LEAD_ID,
                tenant_id=TENANT_ID,
                organization_id=SCHOOL_ORGANIZATION_ID,
                contact_id=SCHOOL_CONTACT_ID,
                source_channel="website",
                source_detail="M7 synthetic demo",
                inquiry_summary=(
                    "A new bilingual school campus needs a production kitchen and dining "
                    "service for approximately 1,800 students and staff."
                ),
                status="qualified",
                priority="high",
                owner_membership_id=SALES_MEMBERSHIP_ID,
                estimated_value=Decimal("4800000000"),
                currency="IDR",
                target_timeline="Campus opening in August 2027",
                project_country_code="ID",
                project_city="Bandung",
                project_type="School production kitchen",
                expected_capacity="1,800 meals per service",
                requirements={
                    "service_scope": ["design", "equipment", "installation", "training"],
                    "decision_maker": "Campus development committee",
                    "floor_plan_available": True,
                },
                qualification_score=Decimal("88"),
            ),
            Lead(
                id=HOSPITAL_LEAD_ID,
                tenant_id=TENANT_ID,
                organization_id=HOSPITAL_ORGANIZATION_ID,
                contact_id=HOSPITAL_CONTACT_ID,
                source_channel="website",
                source_detail="M7 synthetic demo",
                inquiry_summary=(
                    "A 220-bed hospital expansion requires separate patient, staff, and "
                    "therapeutic meal production zones."
                ),
                status="qualifying",
                priority="urgent",
                owner_membership_id=SALES_MEMBERSHIP_ID,
                target_timeline="Target commissioning in Q2 2027",
                project_country_code="ID",
                project_city="Surabaya",
                project_type="Hospital production kitchen",
                expected_capacity="1,200 meals per day",
                requirements={"floor_plan_available": True, "dietary_zoning_required": True},
            ),
            Lead(
                id=FACTORY_LEAD_ID,
                tenant_id=TENANT_ID,
                organization_id=FACTORY_ORGANIZATION_ID,
                contact_id=FACTORY_CONTACT_ID,
                source_channel="manual",
                source_detail="M7 synthetic demo",
                inquiry_summary=(
                    "A manufacturing plant is exploring a staff cafeteria renovation for "
                    "two production shifts. Capacity and budget still require confirmation."
                ),
                status="new",
                priority="normal",
                owner_membership_id=None,
                target_timeline=None,
                project_country_code="ID",
                project_city="Bekasi",
                project_type="Factory cafeteria renovation",
                expected_capacity=None,
                requirements={"operating_shifts": 2},
            ),
            Lead(
                id=CENTRAL_KITCHEN_LEAD_ID,
                tenant_id=TENANT_ID,
                organization_id=CENTRAL_KITCHEN_ORGANIZATION_ID,
                contact_id=CENTRAL_KITCHEN_CONTACT_ID,
                source_channel="website",
                source_detail="M7 synthetic demo",
                inquiry_summary=(
                    "A food-service operator requires a central kitchen for multi-site meal "
                    "preparation, blast chilling, dispatch, and hygiene zoning."
                ),
                status="converted",
                priority="high",
                owner_membership_id=SALES_MEMBERSHIP_ID,
                estimated_value=Decimal("7600000000"),
                currency="IDR",
                target_timeline="Pilot operation in Q4 2027",
                project_country_code="ID",
                project_city="Jakarta",
                project_type="Central kitchen",
                expected_capacity="5,000 meals per day",
                requirements={
                    "service_scope": ["design", "equipment", "installation"],
                    "decision_maker": "Operations steering committee",
                },
                qualification_score=Decimal("91"),
            ),
        ]

        school_result = qualification_result(
            assessment_id="d7400000-0000-4000-8000-000000000001",
            score=88,
            level="A",
            tier="hot",
            summary=(
                "A well-defined school production-kitchen project with confirmed capacity, "
                "timeline, indicative budget, and a named approval group."
            ),
            missing_information=["Confirm final utility loads and tender milestones"],
            recommended_action="Schedule a technical discovery workshop and review the floor plan.",
        )
        hospital_result = qualification_result(
            assessment_id="d7400000-0000-4000-8000-000000000002",
            score=62,
            level="B",
            tier="warm",
            summary=(
                "The hospital project has a credible need, defined capacity, and schedule, "
                "but budget and final decision authority are not yet confirmed."
            ),
            missing_information=["Indicative budget", "Final approval authority"],
            recommended_action="Confirm budget ownership and arrange a clinical workflow review.",
        )
        runs = [
            AgentRun(
                id=UUID("d7300000-0000-4000-8000-000000000001"),
                tenant_id=TENANT_ID,
                agent_configuration_id=AGENT_CONFIGURATION_ID,
                workflow_type="lead_qualification",
                status="succeeded",
                initiated_by_user_id=ADMIN_USER_ID,
                lead_id=SCHOOL_LEAD_ID,
                input_snapshot={"schema_version": "lead_qualification_input_v1", "synthetic": True},
                output_result=school_result,
                provider_type="mock",
                model_id="deterministic-rubric-v1",
                started_at=now - timedelta(days=2, minutes=1),
                completed_at=now - timedelta(days=2),
                correlation_id="demo-school-qualification-001",
                attempt_count=1,
                max_attempts=3,
                last_heartbeat_at=now - timedelta(days=2),
            ),
            AgentRun(
                id=UUID("d7300000-0000-4000-8000-000000000002"),
                tenant_id=TENANT_ID,
                agent_configuration_id=AGENT_CONFIGURATION_ID,
                workflow_type="lead_qualification",
                status="succeeded",
                initiated_by_user_id=ADMIN_USER_ID,
                lead_id=HOSPITAL_LEAD_ID,
                input_snapshot={"schema_version": "lead_qualification_input_v1", "synthetic": True},
                output_result=hospital_result,
                provider_type="mock",
                model_id="deterministic-rubric-v1",
                started_at=now - timedelta(hours=3, minutes=1),
                completed_at=now - timedelta(hours=3),
                correlation_id="demo-hospital-qualification-001",
                attempt_count=1,
                max_attempts=3,
                last_heartbeat_at=now - timedelta(hours=3),
            ),
        ]
        assessments = [
            LeadAssessment(
                id=UUID("d7400000-0000-4000-8000-000000000001"),
                tenant_id=TENANT_ID,
                lead_id=SCHOOL_LEAD_ID,
                assessment_version=1,
                agent_run_id=runs[0].id,
                score=Decimal("88"),
                tier="hot",
                need_summary=school_result["business_summary"],
                qualification=school_result["qualification"],
                recommended_action=school_result["recommended_action"],
                missing_information=school_result["missing_information"],
                confidence=Decimal("0.9000"),
                review_status="approved",
                reviewed_by=ADMIN_USER_ID,
                reviewed_at=now - timedelta(days=1, hours=20),
            ),
            LeadAssessment(
                id=UUID("d7400000-0000-4000-8000-000000000002"),
                tenant_id=TENANT_ID,
                lead_id=HOSPITAL_LEAD_ID,
                assessment_version=1,
                agent_run_id=runs[1].id,
                score=Decimal("62"),
                tier="warm",
                need_summary=hospital_result["business_summary"],
                qualification=hospital_result["qualification"],
                recommended_action=hospital_result["recommended_action"],
                missing_information=hospital_result["missing_information"],
                confidence=Decimal("0.7000"),
                review_status="pending",
            ),
        ]
        opportunity = Opportunity(
            id=UUID("d7500000-0000-4000-8000-000000000001"),
            tenant_id=TENANT_ID,
            organization_id=CENTRAL_KITCHEN_ORGANIZATION_ID,
            primary_contact_id=CENTRAL_KITCHEN_CONTACT_ID,
            source_lead_id=CENTRAL_KITCHEN_LEAD_ID,
            name="Demo Archipelago Central Kitchen Delivery",
            stage="proposal",
            status="open",
            probability=Decimal("55"),
            estimated_value=Decimal("7600000000"),
            currency="IDR",
            expected_close_date=date.today() + timedelta(days=75),
            requirements=leads[3].requirements,
            owner_membership_id=SALES_MEMBERSHIP_ID,
        )
        tasks = [
            Task(
                id=UUID("d7600000-0000-4000-8000-000000000001"),
                tenant_id=TENANT_ID,
                lead_id=HOSPITAL_LEAD_ID,
                title="Confirm hospital project budget owner",
                description="Synthetic demo follow-up; no external message will be sent.",
                status="open",
                priority="urgent",
                assigned_to=SALES_MEMBERSHIP_ID,
                due_at=now - timedelta(days=1),
            ),
            Task(
                id=UUID("d7600000-0000-4000-8000-000000000002"),
                tenant_id=TENANT_ID,
                lead_id=SCHOOL_LEAD_ID,
                title="Review school kitchen floor plan",
                description="Prepare internal questions for the technical discovery workshop.",
                status="open",
                priority="high",
                assigned_to=SALES_MEMBERSHIP_ID,
                due_at=now + timedelta(days=2),
            ),
            Task(
                id=UUID("d7600000-0000-4000-8000-000000000003"),
                tenant_id=TENANT_ID,
                opportunity_id=opportunity.id,
                title="Prepare proposal-stage scope checklist",
                description="Internal preparation only; proposal generation is outside Phase 1.",
                status="in_progress",
                priority="normal",
                assigned_to=SALES_MEMBERSHIP_ID,
                due_at=now + timedelta(days=5),
            ),
        ]
        activities = [
            Activity(
                id=UUID("d7700000-0000-4000-8000-000000000001"),
                tenant_id=TENANT_ID,
                lead_id=SCHOOL_LEAD_ID,
                organization_id=SCHOOL_ORGANIZATION_ID,
                contact_id=SCHOOL_CONTACT_ID,
                activity_type="qualification_reviewed",
                occurred_at=now - timedelta(days=1, hours=20),
                subject="AI qualification approved",
                description="Synthetic demo assessment accepted for sales prioritization.",
                actor_membership_id=ADMIN_MEMBERSHIP_ID,
                metadata_json={"synthetic": True, "score": 88},
            ),
            Activity(
                id=UUID("d7700000-0000-4000-8000-000000000002"),
                tenant_id=TENANT_ID,
                lead_id=HOSPITAL_LEAD_ID,
                organization_id=HOSPITAL_ORGANIZATION_ID,
                contact_id=HOSPITAL_CONTACT_ID,
                activity_type="qualification_completed",
                occurred_at=now - timedelta(hours=3),
                subject="AI qualification ready for review",
                description="Synthetic demo assessment requires a human decision.",
                actor_membership_id=ADMIN_MEMBERSHIP_ID,
                metadata_json={"synthetic": True, "score": 62},
            ),
            Activity(
                id=UUID("d7700000-0000-4000-8000-000000000003"),
                tenant_id=TENANT_ID,
                lead_id=CENTRAL_KITCHEN_LEAD_ID,
                opportunity_id=opportunity.id,
                organization_id=CENTRAL_KITCHEN_ORGANIZATION_ID,
                contact_id=CENTRAL_KITCHEN_CONTACT_ID,
                activity_type="lead_converted",
                occurred_at=now - timedelta(days=4),
                subject="Lead converted to opportunity",
                description="Synthetic central-kitchen opportunity created for the demo pipeline.",
                actor_membership_id=SALES_MEMBERSHIP_ID,
                metadata_json={"synthetic": True},
            ),
        ]

        session.add_all(organizations)
        await session.flush()
        session.add_all(contacts)
        await session.flush()
        session.add_all(leads)
        await session.flush()
        session.add_all(runs)
        await session.flush()
        session.add_all(assessments)
        session.add(opportunity)
        await session.flush()
        session.add_all(tasks)
        session.add_all(activities)
        await session.commit()
        return True


def qualification_result(
    *,
    assessment_id: str,
    score: int,
    level: str,
    tier: str,
    summary: str,
    missing_information: list[str],
    recommended_action: str,
) -> dict[str, object]:
    qualification = {
        "budget_status": "confirmed" if score >= 75 else "unknown",
        "authority_status": "confirmed" if score >= 75 else "partial",
        "need_status": "confirmed",
        "timeline_status": "confirmed",
    }
    return {
        "assessment_id": assessment_id,
        "score": score,
        "qualification_level": level,
        "tier": tier,
        "need_summary": summary,
        "business_summary": summary,
        "qualification": qualification,
        "key_qualification_factors": [
            {"key": key.removesuffix("_status"), "status": value}
            for key, value in qualification.items()
        ],
        "recommended_action": recommended_action,
        "missing_information": missing_information,
        "confidence": 0.9 if score >= 75 else 0.7,
        "review_status": "approved" if score >= 75 else "pending",
    }


async def main() -> None:
    try:
        created = await seed_demo_data()
        print(
            "Synthetic M7 demo data created."
            if created
            else "Synthetic M7 demo data already exists."
        )
    finally:
        await dispose_database()


if __name__ == "__main__":
    asyncio.run(main())
