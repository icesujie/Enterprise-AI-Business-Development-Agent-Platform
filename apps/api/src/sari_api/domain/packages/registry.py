from __future__ import annotations

from sari_api.domain.packages.commercial_kitchen import COMMERCIAL_KITCHEN_PACKAGE
from sari_api.domain.packages.laboratory_animal_facility import (
    LABORATORY_ANIMAL_FACILITY_PACKAGE,
)
from sari_api.domain.packages.models import DomainAgentManifest

DOMAIN_PACKAGES: tuple[DomainAgentManifest, ...] = (
    COMMERCIAL_KITCHEN_PACKAGE,
    LABORATORY_ANIMAL_FACILITY_PACKAGE,
)

PACKAGES_BY_DOMAIN = {package.domain_key: package for package in DOMAIN_PACKAGES}
PACKAGES_BY_AGENT = {package.agent_key: package for package in DOMAIN_PACKAGES}


def validate_domain_packages() -> None:
    if len(PACKAGES_BY_DOMAIN) != len(DOMAIN_PACKAGES):
        raise ValueError("duplicate domain package key")
    if len(PACKAGES_BY_AGENT) != len(DOMAIN_PACKAGES):
        raise ValueError("duplicate domain agent key")
    for package in DOMAIN_PACKAGES:
        package.validate()


def get_domain_package(domain_key: str) -> DomainAgentManifest:
    try:
        return PACKAGES_BY_DOMAIN[domain_key]
    except KeyError as exc:
        raise LookupError("domain package is not installed") from exc


validate_domain_packages()
