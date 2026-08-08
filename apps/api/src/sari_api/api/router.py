from __future__ import annotations

from fastapi import APIRouter

from sari_api.api.routes.health import router as health_router
from sari_api.api.routes.identity import router as identity_router

router = APIRouter()
router.include_router(health_router)
router.include_router(identity_router)
