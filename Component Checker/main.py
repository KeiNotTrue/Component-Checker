"""Component Checker entry point.  Run with:  python main.py"""
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core.catalog import CatalogError
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Component Checker")
    app.setStyle("Fusion")  # consistent base look on every OS; our stylesheet does the rest
    try:
        window = MainWindow()
    except CatalogError as error:
        QMessageBox.critical(None, "Component Checker", f"The hardware catalog could not be loaded.\n\n{error}")
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
