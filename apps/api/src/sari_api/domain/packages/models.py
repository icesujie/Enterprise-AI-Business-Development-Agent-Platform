from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SupportedLocale = Literal["en", "zh-CN", "id"]
QualificationFieldType = Literal["text", "number", "boolean", "choice", "multi_choice"]
CapabilityStatus = Literal["available", "planned"]

SUPPORTED_LOCALES: tuple[SupportedLocale, ...] = ("en", "zh-CN", "id")


@dataclass(frozen=True, slots=True)
class LocalizedText:
    en: str
    zh_cn: str
    id: str

    def for_locale(self, locale: SupportedLocale) -> str:
        if locale == "zh-CN":
            return self.zh_cn
        if locale == "id":
            return self.id
        return self.en


@dataclass(frozen=True, slots=True)
class QualificationField:
    key: str
    label: LocalizedText
    description: LocalizedText
    field_type: QualificationFieldType
    required: bool
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeCategory:
    key: str
    label: LocalizedText
    description: LocalizedText
    expert_review_required: bool = False


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    key: str
    required: bool
    status: CapabilityStatus
    description: LocalizedText


@dataclass(frozen=True, slots=True)
class DomainAgentManifest:
    domain_key: str
    domain_name: LocalizedText
    package_key: str
    package_version: str
    agent_key: str
    agent_name: LocalizedText
    agent_type: str
    implementation_key: str
    business_objectives: tuple[LocalizedText, ...]
    qualification_fields: tuple[QualificationField, ...]
    knowledge_categories: tuple[KnowledgeCategory, ...]
    required_capabilities: tuple[CapabilityRequirement, ...]
    supported_locales: tuple[SupportedLocale, ...] = SUPPORTED_LOCALES
    default_locale: SupportedLocale = "en"
    response_locale_policy: str = "requested_then_tenant_default"

    def validate(self) -> None:
        if self.default_locale not in self.supported_locales:
            raise ValueError("default locale must be supported")
        if not self.supported_locales or not set(self.supported_locales).issubset(
            set(SUPPORTED_LOCALES)
        ):
            raise ValueError("agent locales must be a non-empty supported locale subset")
        self._require_unique(
            "qualification field", [item.key for item in self.qualification_fields]
        )
        self._require_unique("knowledge category", [item.key for item in self.knowledge_categories])
        self._require_unique("capability", [item.key for item in self.required_capabilities])
        if not self.business_objectives:
            raise ValueError("at least one business objective is required")
        if not self.qualification_fields:
            raise ValueError("at least one qualification field is required")

    @staticmethod
    def _require_unique(label: str, keys: list[str]) -> None:
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate {label} key")
