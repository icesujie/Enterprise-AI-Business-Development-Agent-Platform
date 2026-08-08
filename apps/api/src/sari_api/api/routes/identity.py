from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.database import get_session
from sari_api.adapters.identity_repository import SqlAlchemyIdentityRepository
from sari_api.api.dependencies import get_current_principal, require_role
from sari_api.domain.identity import Principal, Role

router = APIRouter(prefix="/api/v1", tags=["identity"])


class WorkspaceResponse(BaseModel):
    id: UUID
    slug: str
    name: str


class CurrentIdentityResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str
    workspace: WorkspaceResponse
    membership_id: UUID
    role: Role
    permissions: list[str]


class MembershipResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: Role
    status: str


@router.get("/me", response_model=CurrentIdentityResponse)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> CurrentIdentityResponse:
    return CurrentIdentityResponse(
        user_id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
        workspace=WorkspaceResponse(
            id=principal.tenant_id,
            slug=principal.tenant_slug,
            name=principal.tenant_name,
        ),
        membership_id=principal.membership_id,
        role=principal.role,
        permissions=sorted(principal.permissions),
    )


@router.get("/memberships", response_model=list[MembershipResponse])
async def memberships(
    principal: Annotated[Principal, Depends(require_role(Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MembershipResponse]:
    rows = await SqlAlchemyIdentityRepository(session).list_memberships(principal.tenant_id)
    return [
        MembershipResponse(
            id=membership_id,
            email=email,
            display_name=display_name,
            role=role,
            status=membership_status,
        )
        for membership_id, email, display_name, role, membership_status in rows
    ]
