"""Main window: sidebar navigation + stacked pages + light/dark theme toggle."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from core.catalog import Catalog
from core.checker import CompatibilityChecker
from . import theme
from .pages.about_page import AboutPage
from .pages.builder_page import BuilderPage
from .pages.math_page import MathPage
from .pages.results_page import ResultsPage
from .state import AppState
from .widgets import make_label

NAV_ITEMS = [  # (label, icon)
    ("Builder", "fa5s.wrench"),
    ("Results", "fa5s.clipboard-check"),
    ("Math View", "fa5s.project-diagram"),
    ("About", "fa5s.info-circle"),
]
BUILDER, RESULTS, MATH, ABOUT = range(4)


class MainWindow(QMainWindow):
    def __init__(self, catalog: Catalog | None = None):
        super().__init__()
        self.setWindowTitle("SystemX · Computer Component Compatibility Checker")
        self.resize(1240, 780)
        self.setMinimumSize(980, 640)

        self.state = AppState(catalog or Catalog(), CompatibilityChecker())

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.builder_page = BuilderPage(self.state, self.check_compatibility)
        self.results_page = ResultsPage(self.state, self.check_compatibility, lambda: self.show_page(BUILDER))
        self.math_page = MathPage(self.state)
        self.about_page = AboutPage()
        self.pages = [self.builder_page, self.results_page, self.math_page, self.about_page]
        for page in self.pages:
            self.stack.addWidget(page)
        layout.addWidget(self.stack, 1)

        theme.load_saved_theme()
        self.apply_theme()
        self.show_page(BUILDER)

    # ---- sidebar ----
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(224)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(6)

        layout.addWidget(make_label("SystemX", "Logo"))
        layout.addWidget(make_label("Compatibility Checker", "LogoSub"))
        layout.addSpacing(18)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []
        for index, (label, _icon) in enumerate(NAV_ITEMS):
            button = QPushButton("  " + label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _c=False, i=index: self.show_page(i))
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)
        layout.addWidget(make_label("Discrete Mathematics\nFinal Project", "SidebarNote"))
        return sidebar

    # ---- actions ----
    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)

    def check_compatibility(self) -> None:
        self.state.run_check()
        self.show_page(RESULTS)

    def toggle_theme(self) -> None:
        theme.set_theme("light" if theme.current_name() == "dark" else "dark")
        self.apply_theme()

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(theme.build_stylesheet())
        for button, (_label, icon_name) in zip(self.nav_buttons, NAV_ITEMS):
            button.setIcon(theme.icon(icon_name, "text_muted", "primary"))
        if theme.current_name() == "dark":
            self.theme_button.setText("  Switch to light mode")
            self.theme_button.setIcon(theme.icon("fa5s.sun", "text"))
        else:
            self.theme_button.setText("  Switch to dark mode")
            self.theme_button.setIcon(theme.icon("fa5s.moon", "text"))
        for page in self.pages:
            page.refresh_theme()
