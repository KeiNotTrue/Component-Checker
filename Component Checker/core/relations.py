"""RELATIONS part of the project.

Math background
---------------
A binary relation R between sets A and B is a subset of the Cartesian product
A × B. We say "a is related to b" when the ordered pair (a, b) ∈ R.

Here every kind of hardware is a set (CPU, Motherboard, ...), and every
compatibility rule is a relation, written in set-builder notation, for example:

    R_CPU_MB = { (c, m) ∈ CPU × Motherboard | c.socket = m.socket }

`Relation.contains(a, b)` answers "is (a, b) ∈ R?" and
`Relation.ordered_pairs(catalog)` lists every ordered pair of R in the catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .models import CATEGORY_LABELS, Component
from .power import estimate_power
from .propositions import (
    form_factor_supported,
    gpu_fits,
    psu_covers_load,
    psu_has_gpu_connectors,
    psu_meets_gpu_recommendation,
    ram_generation_supported,
    socket_matches,
    storage_interface_supported,
)


@dataclass(frozen=True)
class RuleOutcome:
    """Result of testing one relation on concrete components.

    holds: True  -> the components ARE related (pair is in the relation)
           False -> they are NOT related (incompatible)
           None  -> cannot be decided because a needed spec is missing
    """
    holds: Optional[bool]
    reason: str
    missing: tuple = ()


def _need(component: Component, key: str, label: str):
    """A needed spec: (component, label, value). value is None when it is missing."""
    return (component, label, component.spec(key))


def _evaluate(needs, test: Callable[[], bool], ok_text: Callable[[], str],
              bad_text: Callable[[], str]) -> RuleOutcome:
    """Shared flow: refuse to guess when a spec is missing, else run the test.

    A missing specification is NEVER treated as compatible.
    """
    missing = tuple(f"{label} of {c.name}" for c, label, value in needs if value is None)
    if missing:
        return RuleOutcome(None, "Cannot be verified: the catalog does not list the "
                           + "; ".join(missing) + ".", missing)
    holds = test()
    return RuleOutcome(holds, ok_text() if holds else bad_text())


def _pcie_8pin_of_psu(psu: Component):
    connectors = psu.spec("connectors")
    return None if not connectors else connectors.get("pcie_8pin")


# ---- the rules (one per relation) ---------------------------------------

def _rule_cpu_mb(cpu: Component, mb: Component) -> RuleOutcome:
    return _evaluate(
        [_need(cpu, "socket", "CPU socket"), _need(mb, "socket", "motherboard socket")],
        lambda: socket_matches(cpu.spec("socket"), mb.spec("socket")),
        lambda: f"Both use the {cpu.spec('socket')} socket.",
        lambda: (f"The CPU uses the {cpu.spec('socket')} socket, but the motherboard "
                 f"supports the {mb.spec('socket')} socket."),
    )


def _rule_ram_mb(ram: Component, mb: Component) -> RuleOutcome:
    return _evaluate(
        [_need(ram, "ddr", "DDR generation"), _need(mb, "ram_type", "supported RAM type")],
        lambda: ram_generation_supported(ram.spec("ddr"), mb.spec("ram_type")),
        lambda: f"Both use {ram.spec('ddr')} memory.",
        lambda: (f"The RAM is {ram.spec('ddr')}, but the motherboard only supports "
                 f"{mb.spec('ram_type')}."),
    )


def _rule_mb_case(mb: Component, case: Component) -> RuleOutcome:
    return _evaluate(
        [_need(mb, "form_factor", "form factor"), _need(case, "form_factors", "supported form factors")],
        lambda: form_factor_supported(mb.spec("form_factor"), case.spec("form_factors")),
        lambda: f"The case supports {mb.spec('form_factor')} boards.",
        lambda: (f"The motherboard is {mb.spec('form_factor')}, but the case only supports "
                 f"{', '.join(case.spec('form_factors'))}."),
    )


def _rule_gpu_case(gpu: Component, case: Component) -> RuleOutcome:
    return _evaluate(
        [_need(gpu, "length_mm", "GPU length"), _need(case, "max_gpu_mm", "maximum GPU length")],
        lambda: gpu_fits(gpu.spec("length_mm"), case.spec("max_gpu_mm")),
        lambda: (f"The GPU is {gpu.spec('length_mm'):g} mm long and the case allows up to "
                 f"{case.spec('max_gpu_mm'):g} mm."),
        lambda: (f"The GPU is {gpu.spec('length_mm'):g} mm long, but the case only allows up to "
                 f"{case.spec('max_gpu_mm'):g} mm."),
    )


def _rule_power(cpu: Component, gpu: Component, psu: Component) -> RuleOutcome:
    needs = [_need(cpu, "tdp_w", "CPU TDP"), _need(gpu, "board_power_w", "GPU board power"),
             _need(psu, "wattage_w", "PSU wattage")]
    # Estimate only runs when the numbers exist; _evaluate checks that first.
    def estimate():
        return estimate_power(cpu.spec("tdp_w"), gpu.spec("board_power_w"))

    def detail(est):
        return (f"load {est.load_w} W x 1.2 = {est.with_headroom_w} W, "
                f"rounded up to the {est.required_rating_w} W rating")

    return _evaluate(
        needs,
        lambda: psu_covers_load(psu.spec("wattage_w"), estimate().required_rating_w),
        lambda: (f"The PSU is {psu.spec('wattage_w'):g} W and this build needs "
                 f"{estimate().required_rating_w} W ({detail(estimate())})."),
        lambda: (f"The PSU is only {psu.spec('wattage_w'):g} W, but this build needs at least "
                 f"{estimate().required_rating_w} W ({detail(estimate())})."),
    )


def _rule_gpu_psu_rec(gpu: Component, psu: Component) -> RuleOutcome:
    return _evaluate(
        [_need(gpu, "recommended_psu_w", "recommended PSU wattage"), _need(psu, "wattage_w", "PSU wattage")],
        lambda: psu_meets_gpu_recommendation(psu.spec("wattage_w"), gpu.spec("recommended_psu_w")),
        lambda: (f"The PSU is {psu.spec('wattage_w'):g} W; the GPU maker recommends "
                 f"{gpu.spec('recommended_psu_w'):g} W."),
        lambda: (f"The GPU maker recommends at least {gpu.spec('recommended_psu_w'):g} W, "
                 f"but the PSU is only {psu.spec('wattage_w'):g} W."),
    )


def _rule_gpu_psu_conn(gpu: Component, psu: Component) -> RuleOutcome:
    needs = [_need(gpu, "pcie_8pin", "required PCIe 8-pin count"),
             (psu, "PCIe 8-pin connector count", _pcie_8pin_of_psu(psu))]
    return _evaluate(
        needs,
        lambda: psu_has_gpu_connectors(_pcie_8pin_of_psu(psu), gpu.spec("pcie_8pin")),
        lambda: (f"The GPU needs {gpu.spec('pcie_8pin')} PCIe 8-pin connector(s); the PSU "
                 f"provides {_pcie_8pin_of_psu(psu)}."),
        lambda: (f"The GPU needs {gpu.spec('pcie_8pin')} PCIe 8-pin connector(s), but the PSU "
                 f"only provides {_pcie_8pin_of_psu(psu)}."),
    )


def _rule_storage_mb(storage: Component, mb: Component) -> RuleOutcome:
    return _evaluate(
        [_need(storage, "interface", "storage interface"),
         _need(mb, "storage_interfaces", "supported storage interfaces")],
        lambda: storage_interface_supported(storage.spec("interface"), mb.spec("storage_interfaces")),
        lambda: f"The board provides {storage.spec('interface')} connections.",
        lambda: (f"The drive uses {storage.spec('interface')}, but the board only provides "
                 f"{', '.join(mb.spec('storage_interfaces'))}."),
    )


# ---- the relation objects -----------------------------------------------

class Relation:
    """A compatibility relation between 2 (binary) or 3 (ternary) kinds of component."""

    def __init__(self, key: str, title: str, categories: tuple, definition: str,
                 rule: Callable[..., RuleOutcome]):
        self.key = key
        self.title = title
        self.categories = categories      # e.g. ("cpu", "motherboard") -> A × B
        self.definition = definition      # set-builder notation, shown in the Math View
        self._rule = rule

    @property
    def is_binary(self) -> bool:
        return len(self.categories) == 2

    @property
    def set_names(self) -> str:
        return " × ".join(CATEGORY_LABELS[c] for c in self.categories)

    def evaluate(self, *components: Component) -> RuleOutcome:
        return self._rule(*components)

    def contains(self, *components: Component) -> Optional[bool]:
        """Is the tuple (a, b[, c]) a member of this relation? None if undecidable."""
        return self.evaluate(*components).holds

    def ordered_pairs(self, catalog) -> list:
        """All ordered pairs (a, b) in the catalog that belong to this (binary) relation."""
        if not self.is_binary:
            raise ValueError("ordered_pairs is only defined for binary relations")
        first, second = self.categories
        return [(a, b)
                for a in catalog.in_category(first)
                for b in catalog.in_category(second)
                if self.contains(a, b) is True]

    def cartesian_size(self, catalog) -> int:
        """|A × B| for a binary relation."""
        first, second = self.categories
        return len(catalog.in_category(first)) * len(catalog.in_category(second))


RELATION_LIST = [
    Relation("cpu_mb", "CPU ↔ Motherboard (socket)", ("cpu", "motherboard"),
             "{ (c, m) ∈ CPU × Motherboard  |  c.socket = m.socket }", _rule_cpu_mb),
    Relation("ram_mb", "RAM ↔ Motherboard (memory type)", ("ram", "motherboard"),
             "{ (r, m) ∈ RAM × Motherboard  |  r.ddr = m.ram_type }", _rule_ram_mb),
    Relation("mb_case", "Motherboard ↔ Case (form factor)", ("motherboard", "case"),
             "{ (m, k) ∈ Motherboard × Case  |  m.form_factor ∈ k.form_factors }", _rule_mb_case),
    Relation("gpu_case", "GPU ↔ Case (clearance)", ("gpu", "case"),
             "{ (g, k) ∈ GPU × Case  |  g.length ≤ k.max_gpu_length }", _rule_gpu_case),
    Relation("power", "CPU + GPU ↔ PSU (power budget)", ("cpu", "gpu", "psu"),
             "{ (c, g, p) ∈ CPU × GPU × PSU  |  p.wattage ≥ rating_up((c.tdp + g.power + 100) × 1.2) }",
             _rule_power),
    Relation("gpu_psu_rec", "GPU ↔ PSU (recommended wattage)", ("gpu", "psu"),
             "{ (g, p) ∈ GPU × PSU  |  p.wattage ≥ g.recommended_psu }", _rule_gpu_psu_rec),
    Relation("gpu_psu_conn", "GPU ↔ PSU (PCIe connectors)", ("gpu", "psu"),
             "{ (g, p) ∈ GPU × PSU  |  p.pcie_8pin ≥ g.pcie_8pin_needed }", _rule_gpu_psu_conn),
    Relation("storage_mb", "Storage ↔ Motherboard (interface)", ("storage", "motherboard"),
             "{ (s, m) ∈ Storage × Motherboard  |  s.interface ∈ m.storage_interfaces }", _rule_storage_mb),
]

RELATIONS = {r.key: r for r in RELATION_LIST}
BINARY_RELATIONS = [r for r in RELATION_LIST if r.is_binary]
