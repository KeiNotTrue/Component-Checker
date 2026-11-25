"""PROPOSITIONAL LOGIC part of the project.

Each function below is one *atomic proposition*: it takes plain values and
returns a real Python bool (True / False). The compatibility of a build is the
conjunction (AND) of these propositions:

    Compatible = P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W

The functions are deliberately tiny and free of any GUI or catalog code so they
are easy to explain and to test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


# ---- atomic propositions -------------------------------------------------

def socket_matches(cpu_socket: str, board_socket: str) -> bool:
    """P: the CPU socket equals the motherboard socket."""
    return cpu_socket == board_socket


def ram_generation_supported(ram_ddr: str, board_ram_type: str) -> bool:
    """Q: the RAM generation (DDR4/DDR5) is the one the motherboard supports."""
    return ram_ddr == board_ram_type


def form_factor_supported(board_form_factor: str, case_form_factors: Iterable[str]) -> bool:
    """R: the board form factor is a member of the set the case supports (set membership)."""
    return board_form_factor in set(case_form_factors)


def gpu_fits(gpu_length_mm: float, case_max_gpu_mm: float) -> bool:
    """S: the GPU length is at most the case's maximum GPU length."""
    return gpu_length_mm <= case_max_gpu_mm


def psu_covers_load(psu_wattage_w: float, required_rating_w: float) -> bool:
    """T: PSU wattage >= the calculated requirement (see core/power.py)."""
    return psu_wattage_w >= required_rating_w


def psu_meets_gpu_recommendation(psu_wattage_w: float, gpu_recommended_w: float) -> bool:
    """U: PSU wattage >= the PSU wattage the GPU manufacturer recommends."""
    return psu_wattage_w >= gpu_recommended_w


def psu_has_gpu_connectors(psu_pcie_8pin: int, gpu_pcie_8pin: int) -> bool:
    """V: the PSU offers at least as many PCIe 8-pin connectors as the GPU needs."""
    return psu_pcie_8pin >= gpu_pcie_8pin


def storage_interface_supported(storage_interface: str, board_interfaces: Iterable[str]) -> bool:
    """W: the drive interface is in the set of interfaces the board provides."""
    return storage_interface in set(board_interfaces)


# ---- combining propositions ---------------------------------------------

def conjunction(values: Iterable[bool]) -> bool:
    """AND of all values (an empty conjunction is True, as in logic)."""
    result = True
    for value in values:
        result = result and value
    return result


@dataclass(frozen=True)
class PropositionDef:
    """Names one proposition and links it to the relation that decides it."""
    symbol: str
    relation_key: str
    statement: str


PROPOSITION_DEFS = [
    PropositionDef("P", "cpu_mb", "CPU socket matches the motherboard socket"),
    PropositionDef("Q", "ram_mb", "RAM generation is supported by the motherboard"),
    PropositionDef("R", "mb_case", "Motherboard form factor is supported by the case"),
    PropositionDef("S", "gpu_case", "GPU is short enough for the case"),
    PropositionDef("T", "power", "PSU wattage covers the calculated system power requirement"),
    PropositionDef("U", "gpu_psu_rec", "PSU wattage meets the GPU's recommended PSU wattage"),
    PropositionDef("V", "gpu_psu_conn", "PSU has the PCIe 8-pin plugs the GPU needs"),
    PropositionDef("W", "storage_mb", "Storage interface works with the motherboard"),
]


def three_valued_and(values: list[Optional[bool]]) -> Optional[bool]:
    """AND where None means 'unknown'.

    A FALSE anywhere makes the whole AND False (domination law). If nothing is
    False but something is unknown the result is unknown (None).
    """
    known = [v for v in values if v is not None]
    if conjunction(known) is False:
        return False
    return True if len(known) == len(values) else None
