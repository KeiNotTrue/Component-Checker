"""Headless GUI smoke test: drives the real widgets (combos, buttons, menus) without a screen.

Run with:   python -m unittest tests.test_gui_smoke -v      (from the project folder)
"""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from core.models import CATEGORIES
from ui import theme
from ui.main_window import BUILDER, MATH, RESULTS, MainWindow

APP = QApplication.instance() or QApplication([])

GOOD = dict(cpu="cpu-r5-5600", motherboard="mb-asus-b550m-a", ram="ram-corsair-lpx-16-d4",
            gpu="gpu-asus-dual-4060", psu="psu-corsair-cx550", storage="sto-samsung-980",
            case="case-corsair-4000d")


class GuiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        APP.processEvents()
        self.builder = self.window.builder_page
        self.results = self.window.results_page

    def tearDown(self):
        self.window.close()

    def pick(self, category, component_id):
        combo = self.builder.combos[category]
        combo.setCurrentIndex(combo.findData(component_id))

    def pick_all(self, **ids):
        for category, component_id in ids.items():
            self.pick(category, component_id)

    def banner(self):
        return self.results.banner.title.text()

    def test_check_with_nothing_selected_is_incomplete(self):
        self.builder.check_button.click()
        self.assertEqual(self.window.stack.currentIndex(), RESULTS)
        self.assertEqual(self.banner(), "Incomplete Configuration")

    def test_full_compatible_build_via_comboboxes(self):
        self.pick_all(**GOOD)
        self.assertEqual(self.state.selected_count, 7)
        self.assertEqual(self.builder.progress.value(), 7)
        self.builder.check_button.click()
        self.assertEqual(self.banner(), "Compatible")

    @property
    def state(self):
        return self.window.state

    def test_change_part_clears_results_then_recheck_updates(self):
        self.pick_all(**GOOD)
        self.builder.check_button.click()
        self.assertEqual(self.banner(), "Compatible")
        self.window.show_page(BUILDER)
        self.pick("motherboard", "mb-msi-b760m-a-d4")           # change a part
        self.assertIsNone(self.state.report)                    # stale results are cleared
        self.assertEqual(self.banner(), "No results yet")
        self.builder.check_button.click()                       # recheck
        self.assertEqual(self.banner(), "Incompatible")
        self.assertIn("P", [r.symbol for r in self.state.report.incompatible])

    def test_reset_button(self):
        self.pick_all(**GOOD)
        self.builder.check_button.click()
        self.window.show_page(BUILDER)
        self.builder.reset_button.click()
        self.assertEqual(self.state.selected_count, 0)
        for category in CATEGORIES:
            self.assertEqual(self.builder.combos[category].currentIndex(), 0)
        self.assertIsNone(self.state.report)
        self.assertEqual(self.banner(), "No results yet")

    def test_every_sample_in_the_menu_loads_and_gives_expected_status(self):
        actions = self.builder.sample_menu.actions()
        samples = self.state.catalog.sample_builds
        self.assertEqual(len(actions), len(samples))
        for action, sample in zip(actions, samples):
            with self.subTest(sample=sample["name"]):
                self.window.show_page(BUILDER)
                action.trigger()
                self.assertTrue(self.builder.note.text().startswith("Loaded sample"))
                self.builder.check_button.click()
                self.assertEqual(self.banner(), sample["expected"])

    def test_filter_checkbox_hides_incompatible_options(self):
        self.pick("cpu", "cpu-r5-5600")
        combo = self.builder.combos["motherboard"]
        self.assertEqual(combo.count(), 1 + 5)
        self.builder.filter_check.setChecked(True)
        self.assertEqual(combo.count(), 1 + 2)                  # placeholder + two AM4 boards
        self.builder.filter_check.setChecked(False)
        self.assertEqual(combo.count(), 1 + 5)

    def test_spec_panel_lists_selected_components(self):
        self.pick("cpu", "cpu-r5-5600")
        self.pick("gpu", "gpu-asus-dual-4060")
        from ui.widgets import SpecCard
        cards = self.builder.spec_holder.findChildren(SpecCard)
        self.assertEqual(len(cards), 2)

    def test_math_view_follows_report_and_relations(self):
        math = self.window.math_page
        self.pick_all(**GOOD)
        self.builder.check_button.click()
        self.window.show_page(MATH)
        values = [math.logic_table.item(r, 2).text() for r in range(math.logic_table.rowCount())]
        self.assertEqual(values, ["TRUE"] * 8)
        self.assertEqual(math.result_label.text(), "Compatible = TRUE")
        for index in range(math.relation_combo.count()):
            math.relation_combo.setCurrentIndex(index)
            self.assertGreater(math.pairs_table.rowCount(), 0)
            self.assertIn("ordered pairs", math.size_label.text())
        # CPU <-> Motherboard is the first relation: the selected pair is highlighted as a member.
        math.relation_combo.setCurrentIndex(0)
        self.assertIn("YES", math.selected_pair_label.text())

    def test_navigation_and_theme_toggle(self):
        for index, button in enumerate(self.window.nav_buttons):
            button.click()
            self.assertEqual(self.window.stack.currentIndex(), index)
        before = APP.styleSheet()
        self.window.theme_button.click()
        self.assertNotEqual(APP.styleSheet(), before)
        self.window.theme_button.click()
        self.assertEqual(APP.styleSheet(), before)
        theme.set_theme("dark")


if __name__ == "__main__":
    unittest.main()
