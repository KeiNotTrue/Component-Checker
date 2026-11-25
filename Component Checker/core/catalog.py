"""Loads the hardware catalog from data/components.json."""
from __future__ import annotations

import json
from pathlib import Path

from .models import CATEGORIES, Component

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "components.json"


class CatalogError(Exception):
    """Raised when the catalog file is missing or malformed."""


class Catalog:
    def __init__(self, path: Path | str = DEFAULT_PATH):
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CatalogError(f"Catalog file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise CatalogError(f"Catalog file is not valid JSON: {exc}") from exc

        self._by_category: dict[str, list[Component]] = {c: [] for c in CATEGORIES}
        self._by_id: dict[str, Component] = {}

        for category, items in raw.get("components", {}).items():
            if category not in self._by_category:
                raise CatalogError(f"Unknown component category: {category!r}")
            for item in items:
                try:
                    component = Component(
                        id=item["id"],
                        category=category,
                        brand=item["brand"],
                        model=item["model"],
                        specs=item.get("specs", {}),
                        demo=item.get("demo", False),
                        source=item.get("source", ""),
                    )
                except KeyError as exc:
                    raise CatalogError(f"Entry in {category!r} is missing field {exc}") from exc
                if component.id in self._by_id:
                    raise CatalogError(f"Duplicate component id: {component.id}")
                self._by_id[component.id] = component
                self._by_category[category].append(component)

        self.sample_builds: list[dict] = raw.get("sample_builds", [])
        for sample in self.sample_builds:
            for category, cid in sample["selection"].items():
                if cid not in self._by_id:
                    raise CatalogError(f"Sample {sample['name']!r} uses unknown id {cid!r}")

    def in_category(self, category: str) -> list[Component]:
        return list(self._by_category[category])

    def get(self, component_id: str) -> Component:
        return self._by_id[component_id]

    def selection_from_ids(self, ids: dict[str, str]) -> dict[str, Component | None]:
        """Build a full selection dict (None for categories not in `ids`)."""
        return {c: (self._by_id[ids[c]] if c in ids else None) for c in CATEGORIES}
