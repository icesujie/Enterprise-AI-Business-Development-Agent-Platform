from __future__ import annotations

from collections.abc import Callable, Coroutine
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.auth import InvalidAccessTokenError, SupabaseJwtVerifier
from sari_api.adapters.database import get_session
from sari_api.adapters.identity_repository import SqlAlchemyIdentityRepository
from sari_api.application.identity import (
    IdentityService,
    TenantAccessDeniedError,
    TenantContextRequiredError,
    UnknownIdentityError,
)
from sari_api.core.config import get_settings
from sari_api.domain.identity import Principal, Role, TokenIdentity

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_jwt_verifier() -> SupabaseJwtVerifier:
    settings = get_settings()
    return SupabaseJwtVerifier(
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        jwks_url=settings.auth_jwks_url,
        cache_seconds=settings.auth_jwks_cache_seconds,
    )


async def get_token_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    verifier: Annotated[SupabaseJwtVerifier, Depends(get_jwt_verifier)],
) -> TokenIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await verifier.verify(credentials.credentials)
    except InvalidAccessTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_principal(
    identity: Annotated[TokenIdentity, Depends(get_token_identity)],
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: Annotated[UUID | None, Header(alias="X-Tenant-Id")] = None,
) -> Principal:
    try:
        service = IdentityService(SqlAlchemyIdentityRepository(session))
        return await service.resolve(identity, tenant_id)
    except UnknownIdentityError as exc:
        raise HTTPException(
            status_code=403,
            detail="This identity has no active workspace access.",
        ) from exc
    except TenantContextRequiredError as exc:
        raise HTTPException(
            status_code=400,
            detail="Select one of your active workspaces.",
        ) from exc
    except TenantAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail="Workspace access denied.") from exc


def require_role(
    required_role: Role,
) -> Callable[[Principal], Coroutine[Any, Any, Principal]]:
    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.role is not required_role:
            raise HTTPException(status_code=403, detail="This action requires a different role.")
        return principal

    return dependency
