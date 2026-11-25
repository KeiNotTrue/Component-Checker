"""Compatibility checker: evaluates the propositions for a selection of components.

This module ties the two discrete-math ideas together:
  * each proposition (P, Q, R, ...) is decided by testing whether the selected
    components form a pair that belongs to a RELATION (core/relations.py);
  * the overall verdict is the CONJUNCTION of the propositions (core/propositions.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .models import CATEGORIES, CATEGORY_LABELS
from .power import PowerEstimate, estimate_power
from .propositions import PROPOSITION_DEFS, three_valued_and
from .relations import BINARY_RELATIONS, RELATIONS


class Status(Enum):
    COMPATIBLE = "Compatible"
    INCOMPATIBLE = "Incompatible"
    MISSING_INFO = "Missing Information"
    INCOMPLETE = "Incomplete Configuration"

    @property
    def tone(self) -> str:
        """Colour family used by the interface."""
        return {
            Status.COMPATIBLE: "ok",
            Status.INCOMPATIBLE: "bad",
            Status.MISSING_INFO: "warn",
            Status.INCOMPLETE: "neutral",
        }[self]


# State of a single proposition.
TRUE = "TRUE"
FALSE = "FALSE"
MISSING_INFO = "MISSING INFO"
NOT_TESTED = "NOT TESTED"


@dataclass
class PropositionResult:
    symbol: str
    statement: str
    relation_title: str
    categories: tuple
    components: tuple          # the selected components involved (may be shorter than categories)
    state: str                 # TRUE / FALSE / MISSING INFO / NOT TESTED
    reason: str

    @property
    def value(self) -> Optional[bool]:
        """Truth value: True, False, or None when the proposition could not be decided."""
        return {TRUE: True, FALSE: False}.get(self.state)

    @property
    def tone(self) -> str:
        return {TRUE: "ok", FALSE: "bad", MISSING_INFO: "warn", NOT_TESTED: "neutral"}[self.state]

    @property
    def pair_text(self) -> str:
        if len(self.components) == len(self.categories):
            return "  ↔  ".join(c.name for c in self.components)
        return "  ↔  ".join(CATEGORY_LABELS[c] for c in self.categories)


@dataclass
class CheckReport:
    status: Status
    headline: str
    results: list
    not_selected: list                 # labels of categories without a component
    selected_count: int
    power: Optional[PowerEstimate]
    expression: str                    # "P ∧ Q ∧ ..."
    substituted: str                   # "T ∧ F ∧ ?"
    overall_value: Optional[bool]      # value of the whole conjunction (None if undecided)

    @property
    def compatible(self) -> list:
        return [r for r in self.results if r.state == TRUE]

    @property
    def incompatible(self) -> list:
        return [r for r in self.results if r.state == FALSE]

    @property
    def needs_attention(self) -> list:
        return [r for r in self.results if r.state in (MISSING_INFO, NOT_TESTED)]


class CompatibilityChecker:
    """Stateless checker: give it a selection, get a CheckReport."""

    def check(self, selection: dict) -> CheckReport:
        results = [self._evaluate(defn, selection) for defn in PROPOSITION_DEFS]

        not_selected = [CATEGORY_LABELS[c] for c in CATEGORIES if selection.get(c) is None]
        selected_count = len(CATEGORIES) - len(not_selected)

        # Overall value = P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W (None if some are undecided).
        values = [r.value for r in results]
        overall = three_valued_and(values)

        # Status. A definite FALSE wins, then unverifiable specs, then unfinished builds.
        failed = [r for r in results if r.state == FALSE]
        unverifiable = [r for r in results if r.state == MISSING_INFO]
        if failed:
            status = Status.INCOMPATIBLE
            headline = (f"{len(failed)} condition(s) are FALSE: "
                        f"{', '.join(r.symbol for r in failed)}. See the explanations below.")
        elif unverifiable:
            status = Status.MISSING_INFO
            headline = ("Some specifications are not listed in the catalog, so these conditions "
                        f"cannot be verified: {', '.join(r.symbol for r in unverifiable)}.")
        elif not_selected:
            status = Status.INCOMPLETE
            headline = ("The build is not finished. Still to choose: "
                        + ", ".join(not_selected) + ".")
        else:
            status = Status.COMPATIBLE
            headline = f"All {len(results)} compatibility conditions are TRUE for this build."

        power = None
        cpu, gpu = selection.get("cpu"), selection.get("gpu")
        if cpu and gpu and cpu.spec("tdp_w") is not None and gpu.spec("board_power_w") is not None:
            power = estimate_power(cpu.spec("tdp_w"), gpu.spec("board_power_w"))

        symbol = {True: "T", False: "F", None: "?"}
        return CheckReport(
            status=status,
            headline=headline,
            results=results,
            not_selected=not_selected,
            selected_count=selected_count,
            power=power,
            expression=" ∧ ".join(d.symbol for d in PROPOSITION_DEFS),
            substituted=" ∧ ".join(symbol[v] for v in values),
            overall_value=overall,
        )

    @staticmethod
    def _evaluate(defn, selection: dict) -> PropositionResult:
        relation = RELATIONS[defn.relation_key]
        components = tuple(selection.get(c) for c in relation.categories)
        chosen = tuple(c for c in components if c is not None)

        if len(chosen) < len(components):
            absent = [CATEGORY_LABELS[c] for c, comp in zip(relation.categories, components) if comp is None]
            return PropositionResult(defn.symbol, defn.statement, relation.title, relation.categories,
                                     chosen, NOT_TESTED, "Select " + " and ".join(absent) + " to test this rule.")

        outcome = relation.evaluate(*components)
        state = MISSING_INFO if outcome.holds is None else (TRUE if outcome.holds else FALSE)
        return PropositionResult(defn.symbol, defn.statement, relation.title, relation.categories,
                                 chosen, state, outcome.reason)

    @staticmethod
    def compatible_options(catalog, selection: dict, category: str) -> list:
        """Components of `category` that are NOT ruled out by the current selection.

        Uses the binary relations: an option is hidden only when a relation says
        FALSE against an already-selected component. Undecidable (None) options stay
        visible, and the current selection is always kept.
        """
        options = []
        for candidate in catalog.in_category(category):
            keep = candidate is selection.get(category)
            if not keep:
                keep = True
                for relation in BINARY_RELATIONS:
                    if category not in relation.categories:
                        continue
                    other_category = next(c for c in relation.categories if c != category)
                    other = selection.get(other_category)
                    if other is None:
                        continue
                    pair = [candidate if c == category else other for c in relation.categories]
                    if relation.contains(*pair) is False:
                        keep = False
                        break
            if keep:
                options.append(candidate)
        return options
