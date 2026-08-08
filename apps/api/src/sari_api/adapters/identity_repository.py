from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import Tenant, TenantMembership, User
from sari_api.application.identity import (
    TenantAccessDeniedError,
    TenantContextRequiredError,
    UnknownIdentityError,
)
from sari_api.domain.identity import Principal, Role, TokenIdentity


class SqlAlchemyIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_principal(
        self,
        identity: TokenIdentity,
        requested_tenant_id: UUID | None,
    ) -> Principal:
        statement = (
            select(
                User.id,
                User.external_subject,
                User.email,
                User.display_name,
                Tenant.id.label("tenant_id"),
                Tenant.slug,
                Tenant.name,
                TenantMembership.id.label("membership_id"),
                TenantMembership.role,
            )
            .join(TenantMembership, TenantMembership.user_id == User.id)
            .join(Tenant, Tenant.id == TenantMembership.tenant_id)
            .where(
                User.identity_provider == "supabase",
                User.external_subject == identity.subject,
                User.status == "active",
                TenantMembership.status == "active",
                Tenant.status == "active",
            )
        )
        rows: list[RowMapping] = list((await self._session.execute(statement)).mappings().all())
        if not rows:
            raise UnknownIdentityError

        if requested_tenant_id is None:
            if len(rows) != 1:
                raise TenantContextRequiredError
            selected = rows[0]
        else:
            matching_rows = [row for row in rows if row["tenant_id"] == requested_tenant_id]
            if not matching_rows:
                raise TenantAccessDeniedError
            selected = matching_rows[0]

        return Principal(
            user_id=selected["id"],
            external_subject=selected["external_subject"],
            email=selected["email"],
            display_name=selected["display_name"],
            tenant_id=selected["tenant_id"],
            tenant_slug=selected["slug"],
            tenant_name=selected["name"],
            membership_id=selected["membership_id"],
            role=Role(selected["role"]),
        )

    async def list_memberships(self, tenant_id: UUID) -> list[tuple[UUID, str, str, Role, str]]:
        statement = (
            select(
                TenantMembership.id,
                User.email,
                User.display_name,
                TenantMembership.role,
                TenantMembership.status,
            )
            .join(User, User.id == TenantMembership.user_id)
            .where(TenantMembership.tenant_id == tenant_id)
            .order_by(User.display_name)
        )
        rows = (await self._session.execute(statement)).all()
        return [(row.id, row.email, row.display_name, Role(row.role), row.status) for row in rows]
