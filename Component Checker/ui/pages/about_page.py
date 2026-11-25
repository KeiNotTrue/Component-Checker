"""About page: purpose, how it works, limits and credits."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from ..widgets import DISCLAIMER, ScrollColumn, make_card, make_label


def _section(title: str, lines: list[str]):
    card = make_card()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(6)
    layout.addWidget(make_label(title, "SectionTitle"))
    for line in lines:
        layout.addWidget(make_label(line, "", wrap=True))
    return card


class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        root.addWidget(make_label("About Component Checker", "PageTitle"))
        root.addWidget(make_label("Computer Component Compatibility Checker · Discrete Mathematics final project",
                                  "PageSubtitle"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = ScrollColumn(spacing=12)
        layout = holder.column

        layout.addWidget(_section("What it does", [
            "Component Checker helps beginners check whether the PC parts they picked will work together: CPU, "
            "motherboard, RAM, GPU, power supply, storage and case.",
        ]))
        layout.addWidget(_section("The Discrete Mathematics behind it", [
            "Propositional logic: every check is a TRUE/FALSE proposition (P to W) evaluated with Python "
            "Boolean expressions. The build is compatible when P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W is TRUE.",
            "Relations: each kind of part is a set, and each rule is a relation (a subset of a Cartesian "
            "product such as CPU × Motherboard). Two parts are compatible when their ordered pair belongs "
            "to the relation. See the Math View page for the actual pairs.",
        ]))
        layout.addWidget(_section("The rules", [
            "P  CPU socket = motherboard socket.",
            "Q  RAM generation = the generation the motherboard supports.",
            "R  Motherboard form factor is one of the case's supported form factors.",
            "S  GPU length ≤ the case's maximum GPU length.",
            "T  PSU wattage ≥ (CPU TDP + GPU board power + 100 W) × 1.2, rounded up to the next standard "
            "rating (450, 500, 550, 650, 750, 850, 1000, 1200 W). This is a heuristic defined by this project.",
            "U  PSU wattage ≥ the PSU wattage the GPU manufacturer recommends.",
            "V  PSU has at least as many PCIe 8-pin connectors as the GPU needs.",
            "W  Storage interface (SATA or NVMe) is supported by the motherboard.",
        ]))
        layout.addWidget(_section("Result types", [
            "Compatible: all conditions are TRUE.   Incompatible: at least one condition is FALSE.",
            "Missing Information: a needed specification is not listed, so the rule cannot be verified "
            "(it is never assumed to be compatible).   Incomplete Configuration: some parts are not selected yet.",
        ]))
        layout.addWidget(_section("Limits", [DISCLAIMER]))
        layout.addWidget(_section("Credits", [
            "Built with Python, PySide6 (Qt 6) and QtAwesome for icons. Hardware specifications come from the "
            "manufacturer or retailer pages named in each component's Source line.",
        ]))
        layout.addStretch(1)
        scroll.setWidget(holder)
        root.addWidget(scroll, 1)

    def refresh_theme(self) -> None:
        pass
