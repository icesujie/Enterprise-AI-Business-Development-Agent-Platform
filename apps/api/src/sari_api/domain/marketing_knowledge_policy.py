from __future__ import annotations

from typing import Final
from uuid import UUID

MARKETING_CONTENT_AGENT_ID: Final = UUID("61000000-0000-4000-8000-000000000003")
MARKETING_CONTENT_AGENT_KEY: Final = "commercial_kitchen.marketing_content"
MARKETING_CONTENT_CAPABILITY_KEY: Final = "public_marketing_content_generation"
MARKETING_KNOWLEDGE_POLICY_KEY: Final = "public_marketing_v1"
PUBLIC_MARKETING_VISIBILITY: Final = "public_marketing"

ALLOWED_PUBLIC_MARKETING_KNOWLEDGE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "public_company_profile",
        "public_case_study",
        "public_product_service",
        "public_brand_guideline",
        "public_marketing_reference",
    }
)

FORBIDDEN_MARKETING_KNOWLEDGE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "internal_pricing",
        "supplier_information",
        "private_customer_information",
        "crm_record",
        "opportunity_data",
        "internal_sop",
        "internal_engineering_note",
        "confidential_commercial_terms",
        "unpublished_knowledge",
    }
)
