from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, text

from sari_api.adapters.database import session_factory
from sari_api.adapters.enterprise_knowledge_repository import EnterpriseKnowledgeRepository
from sari_api.adapters.knowledge_embedding import build_knowledge_embedding_provider
from sari_api.adapters.knowledge_storage import get_knowledge_storage
from sari_api.adapters.managed_knowledge_processing import ManagedKnowledgeProcessingExecutor
from sari_api.adapters.models import (
    Agent,
    DomainPackage,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeDocument,
)
from sari_api.core.config import get_settings
from sari_api.domain.marketing_knowledge_policy import PUBLIC_MARKETING_VISIBILITY

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

MARKETING_DEMO_ITEMS = (
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-company-profile",
        "Public Marketing Company Profile",
        "Sari Arta Company Profile — Synthetic Public Marketing Demo",
        "company_profile",
        "sari-arta-company-profile-synthetic.md",
        "public_company_profile",
        "en",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-school-case",
        "Public Marketing School Kitchen Case",
        "School Central Kitchen Case — Synthetic Public Marketing Demo",
        "case_study",
        "sari-arta-school-case-synthetic.md",
        "public_case_study",
        "en",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-product-services",
        "Public Marketing Product and Service Information",
        "Commercial Kitchen Product Catalogue — Synthetic Public Marketing Demo",
        "product_catalogue",
        "sari-arta-product-catalogue-synthetic.md",
        "public_product_service",
        "en",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-company-profile-zh",
        "公开营销公司介绍 (中文)",
        "Sari Arta 公司介绍 — 合成公开营销演示",
        "company_profile",
        "sari-arta-company-profile-synthetic.zh-CN.md",
        "public_company_profile",
        "zh-CN",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-school-case-zh",
        "公开营销学校厨房案例 (中文)",
        "学校中央厨房案例 — 合成公开营销演示",
        "case_study",
        "sari-arta-school-case-synthetic.zh-CN.md",
        "public_case_study",
        "zh-CN",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-product-services-zh",
        "公开营销产品与服务 (中文)",
        "商用厨房产品与服务 — 合成公开营销演示",
        "product_catalogue",
        "sari-arta-product-catalogue-synthetic.zh-CN.md",
        "public_product_service",
        "zh-CN",
    ),
    (
        "commercial_kitchen",
        "commercial_kitchen.marketing_content",
        "public-marketing-acceptance-reference-zh",
        "公开营销验收参考 (中文)",
        "Sari Arta 业务验收参考 — 合成公开营销演示",
        "marketing_reference",
        "sari-arta-marketing-acceptance-reference-synthetic.zh-CN.md",
        "public_marketing_reference",
        "zh-CN",
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
        normalized_items = tuple((*item, None, "en") for item in DEMO_ITEMS) + MARKETING_DEMO_ITEMS
        marketing_document_ids: list[UUID] = []
        for (
            domain_key,
            agent_key,
            collection_key,
            collection_name,
            document_title,
            document_type,
            filename,
            knowledge_class,
            language,
        ) in normalized_items:
            content = (DEMO_ROOT / filename).read_bytes()
            phase = "phase-3.2.3.4" if knowledge_class else "phase-2.5.1"
            document_id = uuid5(NAMESPACE_URL, f"{phase}:{collection_key}")
            if knowledge_class:
                marketing_document_ids.append(document_id)
            existing = await session.scalar(
                select(KnowledgeCollection).where(
                    KnowledgeCollection.tenant_id == TENANT_ID,
                    KnowledgeCollection.collection_key == collection_key,
                )
            )
            if existing is not None:
                version_one = await session.scalar(
                    select(KnowledgeDocumentVersion).where(
                        KnowledgeDocumentVersion.tenant_id == TENANT_ID,
                        KnowledgeDocumentVersion.document_id == document_id,
                        KnowledgeDocumentVersion.version_number == 1,
                    )
                )
                if version_one is not None:
                    await storage.put(version_one.object_key, content)
                continue
            domain = await session.scalar(
                select(DomainPackage).where(DomainPackage.domain_key == domain_key)
            )
            agent = await session.scalar(select(Agent).where(Agent.agent_key == agent_key))
            if domain is None or agent is None:
                raise RuntimeError(f"Demo domain agent is not registered: {agent_key}")
            collection = KnowledgeCollection(
                tenant_id=TENANT_ID,
                domain_package_id=domain.id,
                collection_key=collection_key,
                name=collection_name,
                description="Synthetic demonstration knowledge. Not approved for real operations.",
                collection_metadata={
                    "synthetic": True,
                    "demo": phase.replace(".", "_"),
                    **(
                        {"visibility": PUBLIC_MARKETING_VISIBILITY}
                        if knowledge_class
                        else {}
                    ),
                },
                created_by=ADMIN_USER_ID,
            )
            session.add(collection)
            await session.flush()
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
                language=language,
                lifecycle_status="active",
                approval_status="approved",
                current_version_number=1,
                document_metadata={
                    "synthetic": True,
                    "business_use": False,
                    **({"knowledge_class": knowledge_class} if knowledge_class else {}),
                },
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
    await _process_marketing_demo_documents(marketing_document_ids)
    return created


async def _process_marketing_demo_documents(document_ids: list[UUID]) -> None:
    """Create deterministic demo chunks without requiring a separately running worker."""
    settings = get_settings()
    embedding_provider = build_knowledge_embedding_provider(settings)
    executor = ManagedKnowledgeProcessingExecutor(get_knowledge_storage(), embedding_provider)
    for document_id in document_ids:
        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
            completed = await session.scalar(
                select(KnowledgeProcessingRun.id).where(
                    KnowledgeProcessingRun.tenant_id == TENANT_ID,
                    KnowledgeProcessingRun.document_id == document_id,
                    KnowledgeProcessingRun.status == "completed",
                    KnowledgeProcessingRun.embedding_provider
                    == embedding_provider.provider_type,
                    KnowledgeProcessingRun.embedding_model == embedding_provider.model_id,
                )
            )
            if completed is not None:
                continue
            repository = EnterpriseKnowledgeRepository(session, TENANT_ID)
            _, run = await repository.create_processing_run(
                document_id,
                created_by=ADMIN_USER_ID,
                chunk_size=settings.knowledge_chunk_size,
                chunk_overlap=settings.knowledge_chunk_overlap,
                embedding_provider=embedding_provider.provider_type,
                embedding_model=embedding_provider.model_id,
                embedding_dimensions=embedding_provider.dimensions,
                correlation_id=f"demo-marketing-{document_id}",
            )
            run_id = run.id
            await session.commit()
        await executor.execute(run_id, TENANT_ID)
