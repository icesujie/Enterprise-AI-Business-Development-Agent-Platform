from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    ADMIN = "admin"
    SALES = "sales"


ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: frozenset(
        {
            "audit:read",
            "crm:read",
            "crm:write",
            "leads:assign",
            "leads:convert",
            "leads:qualify",
            "memberships:manage",
            "memberships:read",
            "opportunities:manage",
            "tasks:manage",
        }
    ),
    Role.SALES: frozenset(
        {
            "crm:read",
            "crm:write",
            "leads:convert",
            "leads:qualify",
            "opportunities:manage",
            "tasks:manage",
        }
    ),
}


@dataclass(frozen=True, slots=True)
class TokenIdentity:
    subject: str
    email: str | None


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: UUID
    external_subject: str
    email: str
    display_name: str
    tenant_id: UUID
    tenant_slug: str
    tenant_name: str
    membership_id: UUID
    role: Role

    @property
    def permissions(self) -> frozenset[str]:
        return ROLE_PERMISSIONS[self.role]
