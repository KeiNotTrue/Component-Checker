# Component Checker - Computer Component Compatibility Checker

Discrete Mathematics final project, BSIT 2-1, Pamantasan ng Lungsod ng Valenzuela (PLV).
A desktop app (Python + PySide6 + QSS) that tells a beginner whether the PC parts they picked will work together,
and **shows the Discrete Mathematics behind every answer**.

## 1. Description
Pick one CPU, motherboard, RAM kit, GPU, PSU, storage drive and case from a JSON catalog, press **Check Compatibility**
and get one of four results, each with plain-language reasons:

| Result | Meaning |
|---|---|
| Compatible (green) | every rule is TRUE |
| Incompatible (red) | at least one rule is FALSE |
| Missing Information (amber) | a needed spec is not in the catalog, so the rule cannot be verified (never assumed OK) |
| Incomplete Configuration (neutral) | some parts are not selected yet |

**Objectives**
1. Apply propositional logic and relations to a real problem and implement them in working code (not only describe them).
2. Help beginners avoid buying incompatible parts.
3. Make the math visible: the Math View page shows the truth values and the ordered pairs.

**Intended users:** first-time PC builders, students, and anyone checking a parts list before buying.

> **Disclaimer:** results are based only on the specifications stored in `data/components.json` and the rules below.
> They do not cover BIOS versions, cooler clearance, cable lengths, PSU size, etc. Always confirm with the manufacturers.

## 2. Install and run
Requires Python 3.10+.
```
cd PCMatch
python -m venv .venv
.venv\Scripts\activate        (Windows)      source .venv/bin/activate   (Linux/macOS)
pip install -r requirements.txt
python main.py
```
`qtawesome` only supplies icons. The theme (light/dark) toggle is in the sidebar and is remembered.

Tests:
```
python -m unittest discover -s tests -p "test_checker.py"          # 29 logic tests
python -m unittest discover -s tests -p "test_gui_smoke.py"        # 9 GUI tests (set QT_QPA_PLATFORM=offscreen if no display)
```

## 3. How to use
1. **Builder** - choose a part in each dropdown (or **Load Sample** for a ready-made build). The right panel shows the specs of each pick.
   "Show only options compatible with my current picks" filters the dropdowns.
2. **Check Compatibility** - opens **Results** with the banner, the overall expression, the power estimate and every rule with its reason.
3. Change any part and check again (results clear when the selection changes). **Reset** clears everything.
4. **Math View** - the 8 propositions with TRUE/FALSE, and the ordered pairs of any relation.

## 4. The Discrete Mathematics concepts and where they are in the code

### 4.1 Propositional logic  (`core/propositions.py`, `core/checker.py`)
Each rule is a proposition with a truth value:

| | Proposition | Function |
|---|---|---|
| P | CPU socket = motherboard socket | `socket_matches` |
| Q | RAM DDR generation = board's RAM type | `ram_generation_supported` |
| R | board form factor is in the case's supported set | `form_factor_supported` |
| S | GPU length <= case max GPU length | `gpu_fits` |
| T | PSU wattage >= required rating | `psu_covers_load` |
| U | PSU wattage >= GPU recommended PSU | `psu_meets_gpu_recommendation` |
| V | PSU PCIe 8-pin count >= GPU need | `psu_has_gpu_connectors` |
| W | storage interface is in the board's list | `storage_interface_supported` |

**Compatible = P ∧ Q ∧ R ∧ S ∧ T ∧ U ∧ V ∧ W.** `conjunction()` is the plain AND. `three_valued_and()` (used by
`CompatibilityChecker.check`) adds "unknown" for missing specs: a single FALSE makes the result FALSE, otherwise an unknown
keeps it undecided. The Results page prints the expression with the values substituted, e.g. `T ∧ T ∧ T ∧ T ∧ F ∧ F ∧ T ∧ T → FALSE`.
Rule R is also set membership (a ∈ A).

### 4.2 Relations  (`core/relations.py`)
Each kind of part is a set (CPU, Motherboard, ...). A rule is a **relation: a subset of a Cartesian product**, e.g.
`R_CPU_MB = {(c, m) ∈ CPU × Motherboard | c.socket = m.socket}`.
- `Relation.contains(a, b)` - is the ordered pair (a, b) in R? (`None` when a spec is missing)
- `Relation.ordered_pairs(catalog)` - lists every pair in R (shown in Math View, with |R| out of |A × B|)
- 7 binary relations (CPU-MB, RAM-MB, MB-Case, GPU-Case, GPU-PSU recommendation, GPU-PSU connectors, Storage-MB) and
  1 ternary relation (power: CPU × GPU × PSU).
`CompatibilityChecker.compatible_options` uses the relations to filter the dropdowns.

### 4.3 Power rule (rule T, `core/power.py`)
`load = CPU TDP + GPU board power + 100 W` (system overhead), `required = load × 1.2`, then rounded **up** to the next standard
rating in {450, 500, 550, 650, 750, 850, 1000, 1200} W. This is a project-defined heuristic, not a manufacturer figure.
Rules U and V add the GPU maker's recommended PSU wattage and the connector requirement as extra propositions.

## 5. Project structure
```
main.py                 entry point
core/                   no GUI code: models, catalog, power, propositions, relations, checker
ui/                     PySide6 GUI: main_window, state, theme, style_template.qss, widgets, pages/
data/components.json    catalog + 9 sample builds with expected results
tests/                  unittest suites
tools/                  take_screenshots.py, generate_sample_outputs.py
docs/                   SAMPLE_OUTPUTS.md, PRESENTATION_GUIDE.md, screenshots/
```

## 6. Samples and screenshots
- Sample inputs/outputs for all 9 builds: [docs/SAMPLE_OUTPUTS.md](docs/SAMPLE_OUTPUTS.md) (all match their expected result).
- Screenshots (dark and light) are in `docs/screenshots/`: builder, compatible/incompatible/missing/incomplete results, Math View, About.

## 7. Data accuracy
The catalog is a **small sample** for the project. Motherboard, GPU, case and PSU entries (and the Samsung drives) were checked against
manufacturer/retailer pages; each entry has a `source` field. **CPU TDP/socket values, RAM kits and the Seagate drive were entered from
manufacturer knowledge and not re-checked online - re-check them against the vendor pages before submitting.** One demo storage entry
deliberately has no interface so the "Missing Information" result can be demonstrated.

## 8. Credits
Python, PySide6 (Qt 6), QtAwesome. Hardware specs belong to their manufacturers.
