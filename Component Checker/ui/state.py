"""Shared application state: the current selection and the last check report.

The pages never talk to each other directly; they read and change this object
and react to its signals. All compatibility logic stays in the `core` package.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from core.catalog import Catalog
from core.checker import CheckReport, CompatibilityChecker
from core.models import CATEGORIES, Component


class AppState(QObject):
    selection_changed = Signal()
    report_changed = Signal()
    message = Signal(str)        # short note shown under the Builder header

    def __init__(self, catalog: Catalog, checker: CompatibilityChecker):
        super().__init__()
        self.catalog = catalog
        self.checker = checker
        self.selection: dict[str, Component | None] = {c: None for c in CATEGORIES}
        self.report: CheckReport | None = None

    @property
    def selected_count(self) -> int:
        return sum(1 for c in self.selection.values() if c is not None)

    def select(self, category: str, component: Component | None) -> None:
        if self.selection[category] is component:
            return
        self.selection[category] = component
        self._selection_updated()

    def reset(self) -> None:
        self.selection = {c: None for c in CATEGORIES}
        self._selection_updated()
        self.message.emit("Configuration reset. Choose components to start a new build.")

    def load_sample(self, sample: dict) -> None:
        self.selection = self.catalog.selection_from_ids(sample["selection"])
        self._selection_updated()
        self.message.emit(f"Loaded sample: {sample['name']}. {sample['description']}")

    def run_check(self) -> None:
        self.report = self.checker.check(self.selection)
        self.report_changed.emit()

    def _selection_updated(self) -> None:
        # Old results no longer describe the new selection, so clear them.
        self.report = None
        self.selection_changed.emit()
        self.report_changed.emit()
