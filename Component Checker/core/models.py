"""Data model for PC components.

A Component is just a category plus a dictionary of specifications. Keeping the
specs in a dictionary means every compatibility rule reads the *same* structured
data, which is what lets us treat compatibility as a mathematical relation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Order matters: it is the order shown in the interface.
CATEGORIES = ["cpu", "motherboard", "ram", "gpu", "psu", "storage", "case"]

CATEGORY_LABELS = {
    "cpu": "CPU",
    "motherboard": "Motherboard",
    "ram": "RAM",
    "gpu": "GPU",
    "psu": "PSU",
    "storage": "Storage",
    "case": "PC Case",
}

# (spec key, label shown to the user, unit suffix) for each category.
SPEC_FIELDS = {
    "cpu": [("socket", "Socket", ""), ("tdp_w", "TDP", " W")],
    "motherboard": [
        ("chipset", "Chipset", ""),
        ("socket", "CPU socket", ""),
        ("ram_type", "Supported RAM", ""),
        ("form_factor", "Form factor", ""),
        ("storage_interfaces", "Storage interfaces", ""),
    ],
    "ram": [
        ("ddr", "DDR generation", ""),
        ("capacity_gb", "Capacity", " GB"),
        ("kit", "Kit", ""),
        ("speed_mhz", "Speed", " MHz"),
    ],
    "gpu": [
        ("chipset", "GPU chip", ""),
        ("length_mm", "Length", " mm"),
        ("board_power_w", "Board power", " W"),
        ("recommended_psu_w", "Recommended PSU", " W"),
        ("pcie_8pin", "PCIe 8-pin needed", ""),
    ],
    "psu": [("wattage_w", "Wattage", " W"), ("connectors", "Power connectors", "")],
    "storage": [
        ("type", "Storage type", ""),
        ("interface", "Interface", ""),
        ("capacity_gb", "Capacity", " GB"),
    ],
    "case": [
        ("form_factors", "Motherboard form factors", ""),
        ("max_gpu_mm", "Max GPU length", " mm"),
    ],
}

CONNECTOR_LABELS = {
    "atx_24pin": "ATX 24-pin",
    "eps_8pin": "EPS 8-pin (CPU)",
    "pcie_8pin": "PCIe 8-pin",
    "pcie_12v_2x6": "12V-2x6",
}

NOT_LISTED = "Not listed"


def format_spec_value(value: Any, suffix: str = "") -> str:
    """Turn a raw spec value into text for display."""
    if value is None or value == [] or value == "":
        return NOT_LISTED
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        parts = [f"{CONNECTOR_LABELS.get(k, k)} x{n}" for k, n in value.items()]
        return " · ".join(parts)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}{suffix}"


@dataclass(frozen=True, eq=False)  # eq=False: compare by identity, keeps it hashable
class Component:
    id: str
    category: str
    brand: str
    model: str
    specs: dict = field(default_factory=dict)
    demo: bool = False
    source: str = ""

    @property
    def name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def display_name(self) -> str:
        return f"{self.name}  (demo: spec not listed)" if self.demo else self.name

    def spec(self, key: str) -> Optional[Any]:
        """Return a spec value, or None when it is missing or blank.

        A missing spec is NEVER treated as 'compatible'; callers must handle None.
        """
        value = self.specs.get(key)
        if value is None or value == [] or value == "":
            return None
        return value

    def spec_rows(self) -> list[tuple[str, str]]:
        """(label, text) rows for the specification panel."""
        rows = [("Brand", self.brand), ("Model", self.model)]
        for key, label, suffix in SPEC_FIELDS[self.category]:
            rows.append((label, format_spec_value(self.specs.get(key), suffix)))
        return rows
