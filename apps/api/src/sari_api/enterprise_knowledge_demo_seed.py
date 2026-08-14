from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_storage import get_knowledge_storage
from sari_api.adapters.models import (
    Agent,
    DomainPackage,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    ManagedKnowledgeDocument,
)

TENANT_ID = UUID("10000000-0000-4000-8000-000000000001")
ADMIN_USER_ID = UUID("20000000-0000-4000-8000-000000000001")
_configured_demo_root = os.getenv("KNOWLEDGE_DEMO_ROOT")
DEMO_ROOT = (
    Path(_configured_demo_root)
    if _configured_demo_root
    else Path(__file__).resolve().parents[4] / "demo-data" / "knowledge"
)

DEMO_ITEMS = (
    (
        "commercial_kitchen",
        "commercial_kitchen.lead_qualification",
        "company-profile",
        "Company Profile",
        "Sari Arta Company Profile — Synthetic Demo",
        "company_profile",
        "sari-arta-company-profile-synthetic.md",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.lead_qualification",
        "school-kitchen-cases",
        "School Kitchen Cases",
        "School Central Kitchen Case — Synthetic Demo",
        "case_study",
        "sari-arta-school-case-synthetic.md",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.lead_qualification",
        "product-catalogue",
        "Product Catalogue",
        "Commercial Kitchen Product Catalogue — Synthetic Demo",
        "product_catalogue",
        "sari-arta-product-catalogue-synthetic.md",
    ),
    (
        "laboratory_animal_facility",
        "laboratory_animal_facility.ivc_business_development",
        "ivc-product-information",
        "IVC Product Information",
        "IVC Product Overview — Synthetic Demo",
        "product_overview",
        "ivc-product-overview-synthetic.md",
    ),
    (
        "laboratory_animal_facility",
        "laboratory_animal_facility.ivc_business_development",
        "animal-facility-cases",
        "Animal Facility Technical Cases",
        "Laboratory Animal Facility Case — Synthetic Demo",
        "case_study",
        "ivc-facility-case-synthetic.md",
    ),
)


async def seed_enterprise_knowledge_demo() -> bool:
    storage = get_knowledge_storage()
    created = False
    async with session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(TENANT_ID)},
        )
        for (
            domain_key,
            agent_key,
            collection_key,
            collection_name,
            document_title,
            document_type,
            filename,
        ) in DEMO_ITEMS:
            existing = await session.scalar(
                select(KnowledgeCollection).where(
                    KnowledgeCollection.tenant_id == TENANT_ID,
                    KnowledgeCollection.collection_key == collection_key,
                )
            )
            if existing is not None:
                continue
            domain = await session.scalar(
                select(DomainPackage).where(DomainPackage.domain_key == domain_key)
            )
            agent = await session.scalar(select(Agent).where(Agent.agent_key == agent_key))
            if domain is None or agent is None:
                raise RuntimeError(f"Demo domain agent is not registered: {agent_key}")
            content = (DEMO_ROOT / filename).read_bytes()
            collection = KnowledgeCollection(
                tenant_id=TENANT_ID,
                domain_package_id=domain.id,
                collection_key=collection_key,
                name=collection_name,
                description="Synthetic demonstration knowledge. Not approved for real operations.",
                collection_metadata={"synthetic": True, "demo": "phase_2_5_1"},
                created_by=ADMIN_USER_ID,
            )
            session.add(collection)
            await session.flush()
            document_id = uuid5(NAMESPACE_URL, f"phase-2.5.1:{collection_key}")
            object_key = f"{TENANT_ID}/managed/demo/{document_id}-{filename}"
            await storage.put(object_key, content)
            now = datetime.now(UTC)
            document = ManagedKnowledgeDocument(
                id=document_id,
                tenant_id=TENANT_ID,
                domain_package_id=domain.id,
                agent_id=agent.id,
                collection_id=collection.id,
                title=document_title,
                document_type=document_type,
                language="en",
                lifecycle_status="active",
                approval_status="approved",
                current_version_number=1,
                document_metadata={"synthetic": True, "business_use": False},
                approved_by=ADMIN_USER_ID,
                approved_at=now,
                review_note="Synthetic demo fixture only.",
                created_by=ADMIN_USER_ID,
            )
            session.add(document)
            await session.flush()
            version = KnowledgeDocumentVersion(
                tenant_id=TENANT_ID,
                document_id=document.id,
                version_number=1,
                original_filename=filename,
                media_type="text/markdown",
                object_key=object_key,
                content_sha256=hashlib.sha256(content).hexdigest(),
                byte_size=len(content),
                version_metadata={"synthetic": True},
                status="active",
                review_status="approved",
                reviewed_by=ADMIN_USER_ID,
                reviewed_at=now,
                review_note="Synthetic demo fixture only.",
                created_by=ADMIN_USER_ID,
            )
            session.add(version)
            await session.flush()
            document.current_version_id = version.id
            document.published_version_id = version.id
            document.active_version_id = version.id
            document.published_by = ADMIN_USER_ID
            document.published_at = now
            session.add(
                KnowledgeDocumentAgentBinding(
                    tenant_id=TENANT_ID,
                    document_id=document.id,
                    agent_id=agent.id,
                    status="enabled",
                    created_by=ADMIN_USER_ID,
                )
            )
            created = True
        await session.commit()
    return created
