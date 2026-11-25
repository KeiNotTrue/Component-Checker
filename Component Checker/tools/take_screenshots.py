"""Renders the real application off-screen and saves screenshots into docs/screenshots.

Usage (from the project folder):   python tools/take_screenshots.py
Works without a display (uses Qt's offscreen platform); on a normal desktop you can also
just run the app and use your system's screenshot tool.
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from ui import theme
from ui.main_window import ABOUT, BUILDER, MATH, RESULTS, MainWindow

OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def sample(window, name):
    return next(s for s in window.state.catalog.sample_builds if s["name"].startswith(name))


def snap(app, window, filename):
    for _ in range(4):          # let layouts and delayed row-fitting timers settle
        app.processEvents()
        time.sleep(0.08)
    window.grab().save(str(OUT / filename))
    print("saved", filename)


def main():
    app = QApplication([])
    app.setStyle("Fusion")
    window = MainWindow()
    window.resize(1240, 780)
    window.show()

    for mode in ("dark", "light"):
        theme.set_theme(mode)
        window.apply_theme()

        window.state.reset()
        window.show_page(BUILDER)
        snap(app, window, f"{mode}_01_builder_empty.png")

        window.state.load_sample(sample(window, "Budget AM4"))
        window.show_page(BUILDER)
        snap(app, window, f"{mode}_02_builder_filled.png")

        window.check_compatibility()
        snap(app, window, f"{mode}_03_results_compatible.png")
        window.show_page(MATH)
        snap(app, window, f"{mode}_06_math_view_compatible.png")

        window.state.load_sample(sample(window, "Underpowered PSU"))
        window.check_compatibility()
        snap(app, window, f"{mode}_04_results_incompatible.png")

        window.state.load_sample(sample(window, "Missing specification"))
        window.check_compatibility()
        snap(app, window, f"{mode}_05_results_missing_info.png")

        window.state.load_sample(sample(window, "Incomplete"))
        window.check_compatibility()
        snap(app, window, f"{mode}_07_results_incomplete.png")

        window.show_page(MATH)
        snap(app, window, f"{mode}_08_math_view_incomplete.png")
        window.show_page(ABOUT)
        snap(app, window, f"{mode}_09_about.png")

    theme.set_theme("dark")


if __name__ == "__main__":
    main()
