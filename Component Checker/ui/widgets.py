"""Small reusable widgets shared by several pages."""
from __future__ import annotations

import textwrap

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.checker import PropositionResult
from core.models import CATEGORY_LABELS, Component
from . import theme

DISCLAIMER = (
    "Results are based only on the specifications and rules stored in Component Checker's sample catalog. "
    "They do not cover every real-world factor (BIOS versions, CPU cooler clearance, PSU length, "
    "cable lengths, and so on), so always confirm with the manufacturers before buying parts."
)


def set_tone(widget: QWidget, tone: str) -> None:
    """Set the 'tone' property used by the stylesheet and re-apply the style."""
    widget.setProperty("tone", tone)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def make_label(text: str = "", object_name: str = "", wrap: bool = False) -> QLabel:
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    label.setWordWrap(wrap)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def make_card() -> QFrame:
    card = QFrame()
    card.setObjectName("Card")
    return card


class ScrollColumn(QWidget):
    """Vertical column to put inside a QScrollArea.

    Qt does not size a scroll area's content for word-wrapped labels by itself (cards get
    squashed instead of scrolling), so this widget sets its own minimum height from the
    layout's height-for-width whenever its layout or width changes.
    """

    def __init__(self, spacing: int = 10, margins=(0, 0, 6, 0)):
        super().__init__()
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(*margins)
        self.column.setSpacing(spacing)

    def _refit(self) -> None:
        # Wrapped labels need height-for-width; otherwise use the layout's own minimum height.
        height = 0
        if self.column.hasHeightForWidth():
            height = self.column.totalHeightForWidth(self.width())
        height = max(height, self.column.minimumSize().height())
        if height > 0 and height != self.minimumHeight():
            self.setMinimumHeight(height)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refit()

    def event(self, event) -> bool:
        result = super().event(event)
        if event.type() == QEvent.LayoutRequest:
            self._refit()
        return result


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)   # disappears immediately, not on the next event-loop turn
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


class FitFrame(QFrame):
    """A card that never gets squashed below the height its word-wrapped text needs."""

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        layout = self.layout()
        if layout is not None and layout.hasHeightForWidth():
            height = layout.totalHeightForWidth(self.width())
            if height > 0 and height != self.minimumHeight():
                self.setMinimumHeight(height)


class SpecCard(QFrame):
    """Shows the specifications of one selected component."""

    def __init__(self, component: Component):
        super().__init__()
        self.setObjectName("SpecCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(theme.pixmap(theme.CATEGORY_ICONS[component.category], "primary", 20))
        header.addWidget(icon_label)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(make_label(CATEGORY_LABELS[component.category].upper(), "CategoryTag"))
        titles.addWidget(make_label(component.name, "CardTitle"))
        header.addLayout(titles, 1)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(5)
        grid.setColumnStretch(1, 1)
        # Brand/Model are already in the title, so skip the first two rows here.
        # Labels are not word-wrapped (wrapped labels make card heights unreliable); long
        # lists such as connectors are shown one item per line instead.
        for row, (label, text) in enumerate(component.spec_rows()[2:]):
            text = text.replace(" · ", "\n").replace(", ", "\n")
            grid.addWidget(make_label(label, "SpecKey"), row, 0, Qt.AlignTop)
            grid.addWidget(make_label(text, "SpecValue"), row, 1, Qt.AlignTop)
        layout.addLayout(grid)

        if component.source:
            layout.addWidget(make_label("Source: " + textwrap.fill(component.source, 46), "Small"))

        # No label wraps, so the layout's size hint is exact: reserve that height so the
        # card can never be squashed inside a scroll area.
        self.setMinimumHeight(layout.sizeHint().height())


class Banner(QFrame):
    """Large status banner (colour changes with the status)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("Banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)
        self.icon_label = QLabel()
        layout.addWidget(self.icon_label, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        self.title = make_label("", "BannerTitle")
        self.summary = make_label("", "", wrap=True)
        texts.addWidget(self.title)
        texts.addWidget(self.summary)
        layout.addLayout(texts, 1)

    def set_content(self, tone: str, title: str, summary: str) -> None:
        self._tone = tone
        self.icon_label.setPixmap(theme.pixmap(theme.TONE_ICONS[tone], tone if tone != "neutral" else "text_muted", 34))
        self.title.setText(title)
        self.summary.setText(summary)
        set_tone(self, tone)
        set_tone(self.title, tone)

    def refresh_theme(self) -> None:
        if hasattr(self, "_tone"):
            self.set_content(self._tone, self.title.text(), self.summary.text())


class RuleCard(FitFrame):
    """One proposition result: icon, rule statement, components, reason, TRUE/FALSE pill."""

    def __init__(self, result: PropositionResult):
        super().__init__()
        self.setObjectName("RuleCard")
        set_tone(self, result.tone)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setPixmap(theme.pixmap(theme.TONE_ICONS[result.tone],
                                          result.tone if result.tone != "neutral" else "text_muted", 24))
        layout.addWidget(icon_label, 0, Qt.AlignTop)

        texts = QVBoxLayout()
        texts.setSpacing(3)
        texts.addWidget(make_label(f"{result.symbol}  ·  {result.statement}", "CardTitle", wrap=True))
        texts.addWidget(make_label(result.pair_text, "Muted", wrap=True))
        texts.addWidget(make_label(result.reason, "", wrap=True))
        layout.addLayout(texts, 1)

        pill = QLabel(result.state)
        pill.setObjectName("Pill")
        set_tone(pill, result.tone)
        layout.addWidget(pill, 0, Qt.AlignTop)
