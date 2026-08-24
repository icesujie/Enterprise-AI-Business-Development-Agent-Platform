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
            "content:approve",
            "content:archive",
            "content:audit_read",
            "content:create",
            "content:generate",
            "content:edit",
            "content:read",
            "content:review",
            "content:submit_review",
            "crm:read",
            "crm:write",
            "leads:assign",
            "leads:convert",
            "leads:qualify",
            "knowledge:manage",
            "knowledge:upload",
            "knowledge:edit",
            "knowledge:submit_review",
            "knowledge:approve",
            "knowledge:publish",
            "knowledge:archive",
            "knowledge:restore",
            "knowledge:process",
            "knowledge:audit_read",
            "knowledge:retrieve",
            "memberships:manage",
            "memberships:read",
            "opportunities:manage",
            "public_content:approve",
            "public_content:archive",
            "public_content:audit_read",
            "public_content:create",
            "public_content:edit",
            "public_content:publish",
            "public_content:read",
            "public_content:review",
            "public_content:submit_review",
            "tasks:manage",
        }
    ),
    Role.SALES: frozenset(
        {
            "content:create",
            "content:generate",
            "content:edit",
            "content:read",
            "content:submit_review",
            "crm:read",
            "crm:write",
            "leads:convert",
            "leads:qualify",
            "knowledge:retrieve",
            "opportunities:manage",
            "public_content:create",
            "public_content:edit",
            "public_content:read",
            "public_content:submit_review",
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
