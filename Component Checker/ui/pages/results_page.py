"""Results page: overall status, rule-by-rule explanations, power calculation."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.checker import CheckReport
from ..state import AppState
from ..widgets import (
    DISCLAIMER, Banner, RuleCard, ScrollColumn, clear_layout, make_card, make_label, set_tone,
)


class ResultsPage(QWidget):
    def __init__(self, state: AppState, on_check, on_go_builder):
        super().__init__()
        self.state = state
        self._on_check = on_check
        self._on_go_builder = on_go_builder

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label("Compatibility Results", "PageTitle"))
        titles.addWidget(make_label("Each rule is a TRUE / FALSE condition. The build is compatible only "
                                    "when all of them are TRUE.", "PageSubtitle"))
        header.addLayout(titles, 1)
        self.recheck_button = QPushButton("Check Again")
        self.recheck_button.setObjectName("PrimaryButton")
        self.recheck_button.setCursor(Qt.PointingHandCursor)
        self.recheck_button.clicked.connect(on_check)
        header.addWidget(self.recheck_button)
        root.addLayout(header)

        self.banner = Banner()
        root.addWidget(self.banner)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.holder = ScrollColumn()
        self.content = self.holder.column
        self.scroll.setWidget(self.holder)
        root.addWidget(self.scroll, 1)

        root.addWidget(make_label(DISCLAIMER, "Disclaimer", wrap=True))

        state.report_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        report = self.state.report
        clear_layout(self.content)
        self.recheck_button.setVisible(report is not None)
        if report is None:
            self._show_empty()
        else:
            self._show_report(report)
        self.content.addStretch(1)

    def refresh_theme(self) -> None:
        self.banner.refresh_theme()
        self.refresh()

    # ---- empty state ----
    def _show_empty(self) -> None:
        count = self.state.selected_count
        self.banner.set_content(
            "neutral", "No results yet",
            "Choose components in the Builder and press Check Compatibility. "
            f"You have selected {count} of 7 components so far.")
        button = QPushButton("Go to Builder")
        button.setObjectName("SecondaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self._on_go_builder)
        row = QHBoxLayout()
        row.addWidget(button)
        row.addStretch(1)
        self.content.addLayout(row)

    # ---- full report ----
    def _show_report(self, report: CheckReport) -> None:
        self.banner.set_content(report.status.tone, report.status.value, report.headline)

        self._add_expression_card(report)
        if report.power is not None:
            self._add_power_card(report)

        self._add_group("Incompatible", "bad", report.incompatible)
        self._add_group("Compatible", "ok", report.compatible)
        attention = report.needs_attention
        title = "Missing information / incomplete"
        if report.not_selected:
            title += "  (not selected: " + ", ".join(report.not_selected) + ")"
        self._add_group(title, "warn" if any(r.tone == "warn" for r in attention) else "neutral", attention)

    def _add_group(self, title: str, tone: str, results: list) -> None:
        if not results:
            return
        heading = make_label(f"{title}  ·  {len(results)}", "GroupTitle")
        set_tone(heading, tone)
        self.content.addWidget(heading)
        for result in results:
            self.content.addWidget(RuleCard(result))

    def _add_expression_card(self, report: CheckReport) -> None:
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        layout.addWidget(make_label("Overall condition", "CardTitle"))
        layout.addWidget(make_label(f"Compatible = {report.expression}", "Mono", wrap=True))
        value = {True: "TRUE", False: "FALSE", None: "UNDETERMINED"}[report.overall_value]
        layout.addWidget(make_label(f"            = {report.substituted}   →   {value}", "MonoBig", wrap=True))
        layout.addWidget(make_label("T = TRUE, F = FALSE, ? = could not be tested. A single FALSE makes the "
                                    "whole AND FALSE.", "Small", wrap=True))
        self.content.addWidget(card)

    def _add_power_card(self, report: CheckReport) -> None:
        est = report.power
        card = make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        layout.addWidget(make_label("Power requirement (rule T)", "CardTitle"))
        layout.addWidget(make_label(
            f"CPU {est.cpu_tdp_w} W + GPU {est.gpu_power_w} W + system {est.overhead_w} W = {est.load_w} W", "Mono"))
        layout.addWidget(make_label(
            f"{est.load_w} W × 1.2 headroom = {est.with_headroom_w} W  →  next standard rating: "
            f"{est.required_rating_w} W", "Mono", wrap=True))
        psu = self.state.selection.get("psu")
        if psu is not None and psu.spec("wattage_w") is not None:
            layout.addWidget(make_label(f"Selected PSU: {psu.spec('wattage_w'):g} W", "Muted"))
        layout.addWidget(make_label("This is a project-defined estimate, not a manufacturer figure.",
                                    "Small"))
        self.content.addWidget(card)
