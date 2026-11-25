"""Math View page: shows the propositional logic values and the relation ordered pairs."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from core.models import CATEGORY_LABELS
from core.propositions import PROPOSITION_DEFS
from core.relations import BINARY_RELATIONS
from .. import theme
from ..state import AppState
from ..widgets import make_card, make_label


def _make_table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.NoSelection)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.NoFocus)
    table.setTextElideMode(Qt.ElideNone)   # wrap long names instead of cutting them with "..."
    table.setWordWrap(True)
    # Re-fit row heights whenever a column width changes (e.g. the window is resized).
    table.horizontalHeader().sectionResized.connect(lambda *_: table.resizeRowsToContents())
    return table


class MathPage(QWidget):
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)
        root.addWidget(make_label("Math View", "PageTitle"))
        root.addWidget(make_label("See the two Discrete Mathematics ideas behind the checker: propositional "
                                  "logic (TRUE/FALSE conditions) and relations (sets of ordered pairs).",
                                  "PageSubtitle", wrap=True))

        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        # ---------------- left: propositional logic ----------------
        left = make_card()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 18, 20, 18)
        left_layout.setSpacing(10)
        left_layout.addWidget(make_label("Propositional Logic", "SectionTitle"))
        left_layout.addWidget(make_label("Each condition is a Boolean value. The build is compatible when "
                                         "P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W is TRUE.", "Muted", wrap=True))
        self.logic_table = _make_table(["", "Proposition", "Value"])
        self.logic_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.logic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.logic_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.logic_table.setWordWrap(True)
        left_layout.addWidget(self.logic_table, 1)
        self.expression_label = make_label("", "Mono", wrap=True)
        self.result_label = make_label("", "MonoBig", wrap=True)
        left_layout.addWidget(self.expression_label)
        left_layout.addWidget(self.result_label)
        body.addWidget(left, 1)

        # ---------------- right: relations ----------------
        right = make_card()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 18, 20, 18)
        right_layout.setSpacing(10)
        right_layout.addWidget(make_label("Relations", "SectionTitle"))
        right_layout.addWidget(make_label("A relation is a set of ordered pairs (a, b). Two parts are "
                                          "compatible when their pair belongs to the relation.",
                                          "Muted", wrap=True))
        self.relation_combo = QComboBox()
        for relation in BINARY_RELATIONS:
            self.relation_combo.addItem(relation.title, relation.key)
        self.relation_combo.currentIndexChanged.connect(self._refresh_relation)
        right_layout.addWidget(self.relation_combo)
        self.definition_label = make_label("", "Mono", wrap=True)
        self.size_label = make_label("", "Muted", wrap=True)
        right_layout.addWidget(self.definition_label)
        right_layout.addWidget(self.size_label)
        self.pairs_table = _make_table(["", ""])
        self.pairs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.pairs_table, 1)
        self.selected_pair_label = make_label("", "CardTitle", wrap=True)
        right_layout.addWidget(self.selected_pair_label)
        body.addWidget(right, 1)

        state.report_changed.connect(self.refresh)
        state.selection_changed.connect(self._refresh_relation)
        self.refresh()

    def refresh(self) -> None:
        self._refresh_logic()
        self._refresh_relation()

    # Row heights depend on column widths, so recompute them once the window has its real size.
    def _fit_rows(self) -> None:
        self.logic_table.resizeRowsToContents()
        self.pairs_table.resizeRowsToContents()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._fit_rows)
        QTimer.singleShot(60, self._fit_rows)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._fit_rows)
        QTimer.singleShot(60, self._fit_rows)

    def refresh_theme(self) -> None:
        self.refresh()

    # ---- propositional logic table ----
    def _refresh_logic(self) -> None:
        report = self.state.report
        results = {r.symbol: r for r in report.results} if report else {}
        self.logic_table.setRowCount(len(PROPOSITION_DEFS))
        for row, definition in enumerate(PROPOSITION_DEFS):
            result = results.get(definition.symbol)
            if result is None:
                value_text, tone = "—", "text_muted"
            else:
                value_text = {"TRUE": "TRUE", "FALSE": "FALSE"}.get(result.state, "?")
                tone = {"ok": "ok", "bad": "bad", "warn": "warn", "neutral": "text_muted"}[result.tone]
            symbol_item = QTableWidgetItem(definition.symbol)
            symbol_item.setForeground(QBrush(QColor(theme.color("primary"))))
            font = symbol_item.font()
            font.setBold(True)
            symbol_item.setFont(font)
            value_item = QTableWidgetItem(value_text)
            value_item.setForeground(QBrush(QColor(theme.color(tone))))
            value_item.setFont(font)
            value_item.setTextAlignment(Qt.AlignCenter)
            self.logic_table.setItem(row, 0, symbol_item)
            self.logic_table.setItem(row, 1, QTableWidgetItem(definition.statement))
            self.logic_table.setItem(row, 2, value_item)
        self.logic_table.resizeRowsToContents()

        if report is None:
            self.expression_label.setText("Compatible = P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W")
            self.result_label.setText("Press “Check Compatibility” to fill in the values.")
        else:
            value = {True: "TRUE", False: "FALSE", None: "UNDETERMINED"}[report.overall_value]
            self.expression_label.setText(f"Compatible = {report.expression}\n           = {report.substituted}")
            self.result_label.setText(f"Compatible = {value}")

    # ---- relation pair table ----
    def _refresh_relation(self, *_args) -> None:
        key = self.relation_combo.currentData()
        relation = next(r for r in BINARY_RELATIONS if r.key == key)
        first, second = relation.categories
        catalog = self.state.catalog
        pairs = relation.ordered_pairs(catalog)
        total = relation.cartesian_size(catalog)

        self.definition_label.setText(f"R = {relation.definition}")
        self.size_label.setText(f"|R| = {len(pairs)} ordered pairs out of |{relation.set_names}| = {total} possible pairs")
        self.pairs_table.setHorizontalHeaderLabels([f"a  ∈  {CATEGORY_LABELS[first]}",
                                                    f"b  ∈  {CATEGORY_LABELS[second]}"])

        chosen = (self.state.selection.get(first), self.state.selection.get(second))
        self.pairs_table.setRowCount(len(pairs))
        highlight = QBrush(QColor(theme.color("primary_soft")))
        for row, (a, b) in enumerate(pairs):
            for column, component in enumerate((a, b)):
                item = QTableWidgetItem(component.name)
                if chosen[0] is a and chosen[1] is b:
                    item.setBackground(highlight)
                self.pairs_table.setItem(row, column, item)
        self.pairs_table.resizeRowsToContents()

        if chosen[0] is None or chosen[1] is None:
            missing = " and ".join(CATEGORY_LABELS[c] for c, comp in zip((first, second), chosen) if comp is None)
            self.selected_pair_label.setText(f"Select {missing} in the Builder to test your own pair.")
        else:
            holds = relation.contains(*chosen)
            verdict = {True: "YES, the pair is in R (highlighted above).",
                       False: "NO, the pair is not in R.",
                       None: "Cannot be decided: a specification is missing."}[holds]
            self.selected_pair_label.setText(f"({chosen[0].name}, {chosen[1].name}) ∈ R ?   {verdict}")
