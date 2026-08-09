from __future__ import annotations

from fastapi import APIRouter

from sari_api.api.routes.crm import router as crm_router
from sari_api.api.routes.health import router as health_router
from sari_api.api.routes.identity import router as identity_router
from sari_api.api.routes.public_leads import router as public_leads_router
from sari_api.api.routes.qualification import router as qualification_router
from sari_api.api.routes.work import router as work_router

router = APIRouter()
router.include_router(health_router)
router.include_router(identity_router)
router.include_router(crm_router)
router.include_router(public_leads_router)
router.include_router(qualification_router)
router.include_router(work_router)
