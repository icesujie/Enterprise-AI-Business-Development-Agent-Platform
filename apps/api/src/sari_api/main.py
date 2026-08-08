from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sari_api import __version__
from sari_api.adapters.database import dispose_database
from sari_api.api.router import router
from sari_api.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_database()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs" if settings.app_environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.include_router(router)
    return application


app = create_app()

