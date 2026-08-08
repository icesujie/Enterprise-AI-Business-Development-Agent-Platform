from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "sari_api"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def assert_layer_avoids(layer: str, forbidden_prefixes: tuple[str, ...]) -> None:
    for path in (PACKAGE_ROOT / layer).rglob("*.py"):
        forbidden = {
            module
            for module in imported_modules(path)
            if module.startswith(forbidden_prefixes)
        }
        assert not forbidden, f"{path} imports forbidden modules: {sorted(forbidden)}"


def test_domain_layer_is_independent() -> None:
    assert_layer_avoids(
        "domain",
        (
            "sari_api.adapters",
            "sari_api.api",
            "sari_api.application",
            "sari_api.core",
        ),
    )


def test_application_layer_does_not_depend_on_transport_or_adapters() -> None:
    assert_layer_avoids("application", ("sari_api.adapters", "sari_api.api"))

