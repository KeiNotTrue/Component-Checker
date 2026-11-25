"""Tests for the SystemX core logic (no GUI needed).

Run from the project folder with:   python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.catalog import Catalog, CatalogError
from core.checker import FALSE, MISSING_INFO, NOT_TESTED, TRUE, CompatibilityChecker, Status
from core.models import CATEGORIES, Component
from core.power import estimate_power, round_up_to_standard_rating
from core.propositions import (
    conjunction, form_factor_supported, gpu_fits, psu_covers_load, psu_has_gpu_connectors,
    psu_meets_gpu_recommendation, ram_generation_supported, socket_matches,
    storage_interface_supported, three_valued_and,
)
from core.relations import RELATIONS

CATALOG = Catalog()
CHECKER = CompatibilityChecker()


def build(**ids):
    """Selection from catalog ids, e.g. build(cpu="cpu-r5-5600")."""
    return CATALOG.selection_from_ids(ids)


def by_symbol(report):
    return {r.symbol: r for r in report.results}


GOOD = dict(cpu="cpu-r5-5600", motherboard="mb-asus-b550m-a", ram="ram-corsair-lpx-16-d4",
            gpu="gpu-asus-dual-4060", psu="psu-corsair-cx550", storage="sto-samsung-980",
            case="case-corsair-4000d")


class PropositionTests(unittest.TestCase):
    def test_each_atomic_proposition_true_and_false(self):
        self.assertTrue(socket_matches("AM4", "AM4"))
        self.assertFalse(socket_matches("AM4", "LGA1700"))
        self.assertTrue(ram_generation_supported("DDR4", "DDR4"))
        self.assertFalse(ram_generation_supported("DDR4", "DDR5"))
        self.assertTrue(form_factor_supported("Micro-ATX", ["ATX", "Micro-ATX"]))
        self.assertFalse(form_factor_supported("ATX", ["Mini-ITX"]))
        self.assertTrue(gpu_fits(300, 300))          # equal length still fits
        self.assertFalse(gpu_fits(300.1, 300))
        self.assertTrue(psu_covers_load(450, 450))   # equal wattage is enough
        self.assertFalse(psu_covers_load(449, 450))
        self.assertTrue(psu_meets_gpu_recommendation(550, 550))
        self.assertFalse(psu_meets_gpu_recommendation(500, 550))
        self.assertTrue(psu_has_gpu_connectors(2, 2))
        self.assertFalse(psu_has_gpu_connectors(1, 2))
        self.assertTrue(storage_interface_supported("NVMe", ["NVMe", "SATA"]))
        self.assertFalse(storage_interface_supported("NVMe", ["SATA"]))

    def test_conjunction_truth_table(self):
        for a in (True, False):
            for b in (True, False):
                self.assertEqual(conjunction([a, b]), a and b)
        self.assertTrue(conjunction([]))

    def test_three_valued_and(self):
        self.assertTrue(three_valued_and([True, True]))
        self.assertFalse(three_valued_and([True, False, None]))   # FALSE dominates
        self.assertIsNone(three_valued_and([True, None]))


class PowerTests(unittest.TestCase):
    def test_estimates_match_hand_calculation(self):
        e = estimate_power(65, 115)           # 65+115+100 = 280; x1.2 = 336 -> 450
        self.assertEqual((e.load_w, e.with_headroom_w, e.required_rating_w), (280, 336, 450))
        e = estimate_power(125, 160)          # 385; x1.2 = 462 -> 500
        self.assertEqual((e.load_w, e.with_headroom_w, e.required_rating_w), (385, 462, 500))
        e = estimate_power(125, 266)          # 491; x1.2 = 589.2 -> 590 -> 650
        self.assertEqual((e.load_w, e.with_headroom_w, e.required_rating_w), (491, 590, 650))

    def test_rounding_boundaries(self):
        self.assertEqual(round_up_to_standard_rating(450), 450)
        self.assertEqual(round_up_to_standard_rating(451), 500)
        self.assertEqual(round_up_to_standard_rating(551), 650)
        self.assertEqual(round_up_to_standard_rating(1200), 1200)
        self.assertEqual(round_up_to_standard_rating(1201), 1250)  # above the table
        self.assertEqual(estimate_power(100, 175).with_headroom_w, 450)  # exactly 375 x 1.2
        self.assertEqual(estimate_power(100, 176).required_rating_w, 500)  # 376 x 1.2 = 451.2


class RelationTests(unittest.TestCase):
    """Sizes of the relations over the sample catalog (hand-counted)."""

    def pair_count(self, key):
        return len(RELATIONS[key].ordered_pairs(CATALOG))

    def test_ordered_pair_counts(self):
        self.assertEqual(self.pair_count("cpu_mb"), 10)       # 2x2 AM4 + 2x1 AM5 + 2x2 LGA1700
        self.assertEqual(self.pair_count("ram_mb"), 5)        # 1x3 DDR4 + 1x2 DDR5
        self.assertEqual(self.pair_count("mb_case"), 7)       # 5 for 4000D + 1 + 1 (Mini-ITX board)
        self.assertEqual(self.pair_count("gpu_case"), 8)      # only 7800XT/SG13 fails
        self.assertEqual(self.pair_count("gpu_psu_rec"), 4)
        self.assertEqual(self.pair_count("gpu_psu_conn"), 6)
        self.assertEqual(self.pair_count("storage_mb"), 15)   # demo drive is undecidable, so excluded

    def test_cartesian_size(self):
        self.assertEqual(RELATIONS["cpu_mb"].cartesian_size(CATALOG), 30)

    def test_pair_membership_matches_pair_list(self):
        rel = RELATIONS["cpu_mb"]
        pairs = rel.ordered_pairs(CATALOG)
        for cpu in CATALOG.in_category("cpu"):
            for mb in CATALOG.in_category("motherboard"):
                self.assertEqual((cpu, mb) in pairs, rel.contains(cpu, mb))

    def test_ordered_pairs_rejects_ternary(self):
        with self.assertRaises(ValueError):
            RELATIONS["power"].ordered_pairs(CATALOG)

    def test_relation_is_not_symmetric_as_ordered_pairs(self):
        # (cpu, mb) is an ordered pair of CPU x Motherboard; (mb, cpu) is a different kind of tuple.
        cpu, mb = CATALOG.get("cpu-r5-5600"), CATALOG.get("mb-asus-b550m-a")
        self.assertIn((cpu, mb), RELATIONS["cpu_mb"].ordered_pairs(CATALOG))
        self.assertNotIn((mb, cpu), RELATIONS["cpu_mb"].ordered_pairs(CATALOG))


class CheckerTests(unittest.TestCase):
    def test_all_sample_builds_give_expected_status(self):
        for sample in CATALOG.sample_builds:
            with self.subTest(sample=sample["name"]):
                report = CHECKER.check(CATALOG.selection_from_ids(sample["selection"]))
                self.assertEqual(report.status.value, sample["expected"])

    def test_sample_builds_fail_exactly_the_expected_rules(self):
        expected_failures = {
            "Socket mismatch": ["P"],
            "RAM generation mismatch": ["Q"],
            "Board too big for the case": ["R"],
            "GPU too long for the case": ["S"],
            "Underpowered PSU": ["T", "U"],
        }
        for sample in CATALOG.sample_builds:
            if sample["name"] in expected_failures:
                with self.subTest(sample=sample["name"]):
                    report = CHECKER.check(CATALOG.selection_from_ids(sample["selection"]))
                    failed = [r.symbol for r in report.results if r.state == FALSE]
                    self.assertEqual(failed, expected_failures[sample["name"]])

    def test_compatible_build_details(self):
        report = CHECKER.check(build(**GOOD))
        self.assertEqual(report.status, Status.COMPATIBLE)
        self.assertTrue(all(r.state == TRUE for r in report.results))
        self.assertTrue(report.overall_value)
        self.assertEqual(report.substituted, "T ∧ T ∧ T ∧ T ∧ T ∧ T ∧ T ∧ T")
        self.assertEqual(report.power.required_rating_w, 450)

    def test_cpu_motherboard_examples_from_the_brief(self):
        ok = CHECKER.check(build(cpu="cpu-r5-5600", motherboard="mb-asus-b550m-a"))
        self.assertEqual(by_symbol(ok)["P"].state, TRUE)
        self.assertIn("AM4", by_symbol(ok)["P"].reason)
        bad = CHECKER.check(build(cpu="cpu-r5-5600", motherboard="mb-msi-b760m-a-d4"))
        self.assertEqual(by_symbol(bad)["P"].state, FALSE)
        self.assertIn("AM4", by_symbol(bad)["P"].reason)
        self.assertIn("LGA1700", by_symbol(bad)["P"].reason)

    def test_ram_generation_supported_and_unsupported(self):
        ok = CHECKER.check(build(ram="ram-corsair-lpx-16-d4", motherboard="mb-asus-b550m-a"))
        self.assertEqual(by_symbol(ok)["Q"].state, TRUE)
        bad = CHECKER.check(build(ram="ram-kingston-fury-32-d5", motherboard="mb-asus-b550m-a"))
        self.assertEqual(by_symbol(bad)["Q"].state, FALSE)

    def test_gpu_case_clearance(self):
        ok = CHECKER.check(build(gpu="gpu-sapphire-pulse-7800xt", case="case-coolermaster-nr200p"))
        self.assertEqual(by_symbol(ok)["S"].state, TRUE)
        bad = CHECKER.check(build(gpu="gpu-sapphire-pulse-7800xt", case="case-silverstone-sg13"))
        self.assertEqual(by_symbol(bad)["S"].state, FALSE)

    def test_psu_power_rules(self):
        weak = CHECKER.check(build(cpu="cpu-i5-13600k", gpu="gpu-sapphire-pulse-7800xt", psu="psu-corsair-cx550"))
        r = by_symbol(weak)
        self.assertEqual((r["T"].state, r["U"].state, r["V"].state), (FALSE, FALSE, TRUE))
        strong = CHECKER.check(build(cpu="cpu-i5-13600k", gpu="gpu-sapphire-pulse-7800xt", psu="psu-corsair-rm750e"))
        r = by_symbol(strong)
        self.assertEqual((r["T"].state, r["U"].state, r["V"].state), (TRUE, TRUE, TRUE))

    def test_empty_selection_is_incomplete(self):
        report = CHECKER.check(build())
        self.assertEqual(report.status, Status.INCOMPLETE)
        self.assertTrue(all(r.state == NOT_TESTED for r in report.results))
        self.assertEqual(report.selected_count, 0)
        self.assertEqual(len(report.not_selected), 7)
        self.assertIsNone(report.overall_value)

    def test_partial_build_tests_only_what_it_can(self):
        report = CHECKER.check(build(cpu="cpu-r5-5600", motherboard="mb-asus-b550m-a"))
        self.assertEqual(report.status, Status.INCOMPLETE)
        self.assertEqual(by_symbol(report)["P"].state, TRUE)
        self.assertEqual(by_symbol(report)["Q"].state, NOT_TESTED)

    def test_missing_spec_is_not_treated_as_compatible(self):
        report = CHECKER.check(build(**{**GOOD, "storage": "sto-demo-unlisted"}))
        self.assertEqual(by_symbol(report)["W"].state, MISSING_INFO)
        self.assertEqual(report.status, Status.MISSING_INFO)
        self.assertIsNone(report.overall_value)

    def test_definite_failure_wins_over_missing_info(self):
        report = CHECKER.check(build(**{**GOOD, "storage": "sto-demo-unlisted",
                                         "motherboard": "mb-msi-b760m-a-d4"}))
        self.assertEqual(report.status, Status.INCOMPATIBLE)
        self.assertFalse(report.overall_value)

    def test_blank_spec_values_count_as_missing(self):
        # Synthetic parts: blank string and empty list are "not listed", not "matching".
        cpu = Component("x1", "cpu", "Test", "Blank CPU", {"socket": "", "tdp_w": 65})
        board = Component("x2", "motherboard", "Test", "Board", {"socket": "AM4"})
        outcome = RELATIONS["cpu_mb"].evaluate(cpu, board)
        self.assertIsNone(outcome.holds)
        case = Component("x3", "case", "Test", "No list", {"form_factors": [], "max_gpu_mm": 300})
        mb = CATALOG.get("mb-asus-b550m-a")
        self.assertIsNone(RELATIONS["mb_case"].contains(mb, case))

    def test_storage_interface_not_supported_by_board(self):
        sata_only_board = Component("x4", "motherboard", "Test", "SATA only",
                                    {"storage_interfaces": ["SATA"]})
        nvme = CATALOG.get("sto-samsung-980")
        self.assertFalse(RELATIONS["storage_mb"].contains(nvme, sata_only_board))

    def test_psu_without_pcie_connectors_info(self):
        psu = Component("x5", "psu", "Test", "No connector info", {"wattage_w": 600})
        gpu = CATALOG.get("gpu-asus-dual-4060")
        self.assertIsNone(RELATIONS["gpu_psu_conn"].contains(gpu, psu))

    def test_zero_connectors_is_a_real_value_not_missing(self):
        psu = Component("x6", "psu", "Test", "No PCIe", {"wattage_w": 600, "connectors": {"pcie_8pin": 0}})
        gpu = CATALOG.get("gpu-asus-dual-4060")
        self.assertFalse(RELATIONS["gpu_psu_conn"].contains(gpu, psu))

    def test_change_reset_and_recheck(self):
        selection = build(**{**GOOD, "motherboard": "mb-msi-b760m-a-d4"})
        self.assertEqual(CHECKER.check(selection).status, Status.INCOMPATIBLE)
        selection["motherboard"] = CATALOG.get("mb-asus-b550m-a")      # change one part
        self.assertEqual(CHECKER.check(selection).status, Status.COMPATIBLE)
        selection = build()                                             # reset
        self.assertEqual(CHECKER.check(selection).status, Status.INCOMPLETE)

    def test_compatible_options_filter(self):
        selection = build(cpu="cpu-r5-5600")
        names = {c.id for c in CHECKER.compatible_options(CATALOG, selection, "motherboard")}
        self.assertEqual(names, {"mb-asus-b550m-a", "mb-asus-b550i"})   # AM4 boards only
        # The current selection is never hidden, even if it conflicts.
        selection = build(cpu="cpu-r5-5600", motherboard="mb-msi-b760m-a-d4")
        ids = {c.id for c in CHECKER.compatible_options(CATALOG, selection, "motherboard")}
        self.assertIn("mb-msi-b760m-a-d4", ids)
        # With nothing selected, nothing is hidden.
        self.assertEqual(len(CHECKER.compatible_options(CATALOG, build(), "cpu")), 6)


class CatalogTests(unittest.TestCase):
    def test_catalog_has_every_category(self):
        for category in CATEGORIES:
            self.assertGreater(len(CATALOG.in_category(category)), 0, category)

    def test_missing_file_gives_clear_error(self):
        with self.assertRaises(CatalogError):
            Catalog("does-not-exist.json")


if __name__ == "__main__":
    unittest.main()
