"""Builder page: choose one component per category and view its specifications."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QProgressBar,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from core.models import CATEGORIES, CATEGORY_LABELS
from .. import theme
from ..state import AppState
from ..widgets import ScrollColumn, SpecCard, clear_layout, make_card, make_label


class BuilderPage(QWidget):
    def __init__(self, state: AppState, on_check):
        super().__init__()
        self.state = state
        self._syncing = False
        self.combos: dict[str, QComboBox] = {}
        self.row_icons: dict[str, QLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # ---- header ----
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(make_label("Build Your PC", "PageTitle"))
        titles.addWidget(make_label("Pick one part per category, then check how well they work together.",
                                    "PageSubtitle"))
        header.addLayout(titles, 1)

        self.sample_button = QPushButton("Load Sample  ▾")
        self.sample_button.setObjectName("SecondaryButton")
        self.sample_button.setCursor(Qt.PointingHandCursor)
        self.sample_menu = QMenu(self.sample_button)
        for sample in state.catalog.sample_builds:
            action = QAction(sample["name"], self.sample_menu)
            action.triggered.connect(lambda _checked=False, s=sample: state.load_sample(s))
            self.sample_menu.addAction(action)
        self.sample_button.setMenu(self.sample_menu)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("SecondaryButton")
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(state.reset)

        self.check_button = QPushButton("Check Compatibility")
        self.check_button.setObjectName("PrimaryButton")
        self.check_button.setCursor(Qt.PointingHandCursor)
        self.check_button.clicked.connect(on_check)

        for button in (self.sample_button, self.reset_button, self.check_button):
            header.addWidget(button)
        header.setSpacing(10)
        root.addLayout(header)

        self.note = make_label("", "Muted", wrap=True)
        self.note.hide()
        root.addWidget(self.note)

        # ---- body: selection card (left) + specification panel (right) ----
        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        selection_card = make_card()
        card_layout = QVBoxLayout(selection_card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)
        card_layout.addWidget(make_label("Components", "SectionTitle"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(2, 1)
        for row, category in enumerate(CATEGORIES):
            icon_label = QLabel()
            self.row_icons[category] = icon_label
            grid.addWidget(icon_label, row, 0)
            grid.addWidget(make_label(CATEGORY_LABELS[category], "CardTitle"), row, 1)
            combo = QComboBox()
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(18)
            combo.setCursor(Qt.PointingHandCursor)
            combo.currentIndexChanged.connect(lambda _i, c=category: self._on_combo_changed(c))
            self.combos[category] = combo
            grid.addWidget(combo, row, 2)
        card_layout.addLayout(grid)

        self.filter_check = QCheckBox("Show only options compatible with my current picks")
        self.filter_check.setCursor(Qt.PointingHandCursor)
        self.filter_check.toggled.connect(self._sync_from_state)
        card_layout.addWidget(self.filter_check)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, len(CATEGORIES))
        self.progress.setTextVisible(False)
        self.progress_label = make_label("", "Muted")
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.progress_label)
        card_layout.addLayout(progress_row)
        card_layout.addStretch(1)
        body.addWidget(selection_card, 3)

        # specification panel
        spec_wrapper = QVBoxLayout()
        spec_wrapper.setSpacing(10)
        spec_wrapper.addWidget(make_label("Selected component specifications", "SectionTitle"))
        self.spec_scroll = QScrollArea()
        self.spec_scroll.setWidgetResizable(True)
        self.spec_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.spec_holder = ScrollColumn()
        self.spec_layout = self.spec_holder.column
        self.spec_scroll.setWidget(self.spec_holder)
        spec_wrapper.addWidget(self.spec_scroll, 1)
        body.addLayout(spec_wrapper, 2)

        state.selection_changed.connect(self._sync_from_state)
        state.message.connect(self._show_note)
        self.refresh_theme()
        self._sync_from_state()

    # ---- reacting to the user ----
    def _on_combo_changed(self, category: str) -> None:
        if self._syncing:
            return
        component_id = self.combos[category].currentData()
        component = self.state.catalog.get(component_id) if component_id else None
        self.note.hide()
        self.state.select(category, component)

    def _show_note(self, text: str) -> None:
        self.note.setText(text)
        self.note.show()

    # ---- keeping the widgets in step with the state ----
    def _sync_from_state(self, *_args) -> None:
        self._syncing = True
        try:
            filtering = self.filter_check.isChecked()
            for category in CATEGORIES:
                combo = self.combos[category]
                selected = self.state.selection[category]
                if filtering:
                    options = self.state.checker.compatible_options(
                        self.state.catalog, self.state.selection, category)
                else:
                    options = self.state.catalog.in_category(category)
                combo.blockSignals(True)
                combo.clear()
                combo.addItem(f"Select {CATEGORY_LABELS[category]}…", None)
                for component in options:
                    combo.addItem(component.display_name, component.id)
                combo.setCurrentIndex(combo.findData(selected.id) if selected else 0)
                combo.blockSignals(False)
        finally:
            self._syncing = False

        count = self.state.selected_count
        self.progress.setValue(count)
        self.progress_label.setText(f"{count} of {len(CATEGORIES)} selected")
        self._rebuild_spec_panel()

    def _rebuild_spec_panel(self) -> None:
        clear_layout(self.spec_layout)
        any_selected = False
        for category in CATEGORIES:
            component = self.state.selection[category]
            if component is not None:
                any_selected = True
                self.spec_layout.addWidget(SpecCard(component))
        if not any_selected:
            empty = make_label("Select a component to see its specifications here.", "Muted", wrap=True)
            empty.setAlignment(Qt.AlignCenter)
            self.spec_layout.addWidget(empty)
        self.spec_layout.addStretch(1)

    def refresh_theme(self) -> None:
        for category, label in self.row_icons.items():
            label.setPixmap(theme.pixmap(theme.CATEGORY_ICONS[category], "primary", 22))
        self.check_button.setIcon(theme.icon("fa5s.clipboard-check", "primary_text"))
        self.reset_button.setIcon(theme.icon("fa5s.undo", "text"))
        self.sample_button.setIcon(theme.icon("fa5s.flask", "text"))
        if hasattr(self, "spec_layout"):
            self._rebuild_spec_panel()
