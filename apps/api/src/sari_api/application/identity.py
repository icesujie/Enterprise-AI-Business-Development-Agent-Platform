from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sari_api.domain.identity import Principal, TokenIdentity


class IdentityError(Exception):
    """Base class for safe identity-resolution failures."""


class UnknownIdentityError(IdentityError):
    pass


class TenantContextRequiredError(IdentityError):
    pass


class TenantAccessDeniedError(IdentityError):
    pass


class IdentityRepository(Protocol):
    async def resolve_principal(
        self,
        identity: TokenIdentity,
        requested_tenant_id: UUID | None,
    ) -> Principal: ...


class IdentityService:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def resolve(
        self,
        identity: TokenIdentity,
        requested_tenant_id: UUID | None,
    ) -> Principal:
        return await self._repository.resolve_principal(identity, requested_tenant_id)
