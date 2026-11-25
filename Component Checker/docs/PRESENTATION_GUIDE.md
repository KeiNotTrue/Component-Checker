# Component Checker presentation guide (about 7-10 minutes)

1. **Problem (1 min)** - Beginners buy parts that do not fit or work together. Component Checker checks the combination first.
2. **Demo - good build (1 min)** - Builder > Load Sample > "Budget AM4" > Check. Point at the green banner and the 8 TRUE rules.
3. **Demo - bad build (2 min)** - Load "Underpowered PSU" > Check. Show the red banner, the power card
   (491 W x 1.2 = 590 W -> 650 W needed, PSU is 550 W) and the FALSE rules T and U with reasons.
4. **Other results (1 min)** - "Missing specification" (amber, never assumed compatible) and "Incomplete build".
5. **Concept 1: propositional logic (2 min)** - Open Math View. P to W are propositions; Compatible = P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W.
   One FALSE makes the whole conjunction FALSE. Show the substituted expression. Code: `core/propositions.py`, `checker.py`.
6. **Concept 2: relations (2 min)** - Pick "CPU <-> Motherboard (socket)". A relation is a subset of CPU × Motherboard; show |R| out of |A × B|
   and the highlighted pair of the user's selection. Mention the ternary power relation. Code: `core/relations.py`.
7. **Wrap-up (30 s)** - Tests (29 + 9), light/dark theme, limits (catalog-based; not every real-world factor).

**Likely questions**
- *Why is a missing spec not "compatible"?* The conjunction cannot be verified; assuming TRUE would be unsafe. It is shown as Missing Information.
- *Where is the math, not just if-statements?* Each rule is a Boolean proposition and a relation object with `contains()` and `ordered_pairs()`; the Math View prints them.
- *Where does 1.2 and 100 W come from?* A project-defined safety heuristic, rounded up to standard PSU sizes; it is labeled as an estimate.
- *Can it be wrong?* Yes, it only knows the catalog; always confirm with manufacturers.
