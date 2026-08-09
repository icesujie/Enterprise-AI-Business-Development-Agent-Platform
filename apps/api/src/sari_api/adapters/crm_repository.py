from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import Contact, Lead, Organization

CrmModel = TypeVar("CrmModel", Organization, Contact, Lead)


class CrmNotFoundError(Exception):
    pass


class VersionConflictError(Exception):
    pass


class SqlAlchemyCrmRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def list_organizations(self, search: str | None, limit: int) -> list[Organization]:
        statement = select(Organization).where(
            Organization.tenant_id == self._tenant_id,
            Organization.deleted_at.is_(None),
        )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Organization.display_name.ilike(pattern),
                    Organization.legal_name.ilike(pattern),
                    Organization.domain.ilike(pattern),
                )
            )
        result = await self._session.scalars(
            statement.order_by(Organization.display_name).limit(limit)
        )
        return list(result.all())

    async def list_organizations_with_contact_counts(
        self, search: str | None, limit: int
    ) -> list[tuple[Organization, int]]:
        statement = (
            select(Organization, func.count(Contact.id))
            .outerjoin(
                Contact,
                and_(
                    Contact.organization_id == Organization.id,
                    Contact.tenant_id == self._tenant_id,
                    Contact.deleted_at.is_(None),
                ),
            )
            .where(
                Organization.tenant_id == self._tenant_id,
                Organization.deleted_at.is_(None),
            )
        )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Organization.display_name.ilike(pattern),
                    Organization.legal_name.ilike(pattern),
                    Organization.domain.ilike(pattern),
                )
            )
        rows = await self._session.execute(
            statement.group_by(Organization.id).order_by(Organization.display_name).limit(limit)
        )
        return [(organization, int(contact_count)) for organization, contact_count in rows.all()]

    async def list_contacts(
        self, search: str | None, organization_id: UUID | None, limit: int
    ) -> list[Contact]:
        statement = (
            select(Contact)
            .outerjoin(
                Organization,
                and_(
                    Organization.id == Contact.organization_id,
                    Organization.tenant_id == self._tenant_id,
                    Organization.deleted_at.is_(None),
                ),
            )
            .where(
                Contact.tenant_id == self._tenant_id,
                Contact.deleted_at.is_(None),
            )
        )
        if organization_id:
            statement = statement.where(Contact.organization_id == organization_id)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Contact.first_name.ilike(pattern),
                    Contact.last_name.ilike(pattern),
                    Contact.email.ilike(pattern),
                    Contact.phone_e164.ilike(pattern),
                    Organization.display_name.ilike(pattern),
                    Organization.legal_name.ilike(pattern),
                )
            )
        result = await self._session.scalars(
            statement.order_by(Contact.created_at.desc()).limit(limit)
        )
        return list(result.all())

    async def list_leads(
        self,
        *,
        search: str | None,
        status: str | None,
        priority: str | None,
        owner_id: UUID | None,
        created_before: datetime | None,
        limit: int,
    ) -> list[Lead]:
        statement = select(Lead).where(Lead.tenant_id == self._tenant_id, Lead.deleted_at.is_(None))
        if search:
            statement = statement.where(Lead.inquiry_summary.ilike(f"%{search.strip()}%"))
        if status:
            statement = statement.where(Lead.status == status)
        if priority:
            statement = statement.where(Lead.priority == priority)
        if owner_id:
            statement = statement.where(Lead.owner_membership_id == owner_id)
        if created_before:
            statement = statement.where(Lead.created_at < created_before)
        result = await self._session.scalars(
            statement.order_by(Lead.created_at.desc(), Lead.id.desc()).limit(limit)
        )
        return list(result.all())

    async def get_organization(self, entity_id: UUID, *, for_update: bool = False) -> Organization:
        return await self._get(Organization, entity_id, for_update=for_update)

    async def get_contact(self, entity_id: UUID, *, for_update: bool = False) -> Contact:
        return await self._get(Contact, entity_id, for_update=for_update)

    async def get_lead(self, entity_id: UUID, *, for_update: bool = False) -> Lead:
        return await self._get(Lead, entity_id, for_update=for_update)

    async def _get(
        self,
        model: type[CrmModel],
        entity_id: UUID,
        *,
        for_update: bool,
    ) -> CrmModel:
        statement: Select[tuple[CrmModel]] = select(model).where(
            model.id == entity_id,
            model.tenant_id == self._tenant_id,
            model.deleted_at.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        entity = await self._session.scalar(statement)
        if entity is None:
            raise CrmNotFoundError
        return entity

    async def add(self, entity: CrmModel) -> CrmModel:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def validate_links(
        self,
        organization_id: UUID | None,
        contact_id: UUID | None,
    ) -> None:
        if organization_id:
            await self.get_organization(organization_id)
        if contact_id:
            contact = await self.get_contact(contact_id)
            if organization_id and contact.organization_id not in {None, organization_id}:
                raise CrmNotFoundError

    async def duplicate_warnings(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        domain: str | None = None,
    ) -> list[str]:
        warnings: list[str] = []
        if email and await self._session.scalar(
            select(func.count())
            .select_from(Contact)
            .where(
                Contact.tenant_id == self._tenant_id,
                Contact.deleted_at.is_(None),
                func.lower(Contact.email) == email.lower(),
            )
        ):
            warnings.append("A contact with this email already exists.")
        if phone and await self._session.scalar(
            select(func.count())
            .select_from(Contact)
            .where(
                Contact.tenant_id == self._tenant_id,
                Contact.deleted_at.is_(None),
                Contact.phone_e164 == phone,
            )
        ):
            warnings.append("A contact with this phone number already exists.")
        if domain and await self._session.scalar(
            select(func.count())
            .select_from(Organization)
            .where(
                Organization.tenant_id == self._tenant_id,
                Organization.deleted_at.is_(None),
                func.lower(Organization.domain) == domain.lower(),
            )
        ):
            warnings.append("An organization with this domain already exists.")
        return warnings

    @staticmethod
    def apply_versioned_update(
        entity: CrmModel, expected_version: int, changes: dict[str, Any]
    ) -> None:
        if entity.version != expected_version:
            raise VersionConflictError
        for field, value in changes.items():
            setattr(entity, field, value)
        entity.version += 1

    @staticmethod
    def soft_delete(entity: CrmModel, expected_version: int, now: datetime) -> None:
        if entity.version != expected_version:
            raise VersionConflictError
        entity.deleted_at = now
        entity.version += 1
