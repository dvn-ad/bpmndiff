# bpmndiff — BPMN/XPDL process comparison prototype

A dependency-free Python prototype for comparing business process models
across formats. It implements the pipeline described in
[`docs/overview.md`](docs/overview.md) and the follow-up requirements in
[`docs/feedback.md`](docs/feedback.md). The full taxonomy of detectable
operations — and which scope aspect each one maps to — lives in
[`docs/taxonomy.md`](docs/taxonomy.md):

```
parse & normalise (drop layout)
        │
        ▼
tiered element alignment (exact → lexical → semantic → optional LLM)
        │
        ▼
SESE-style region decomposition
        │
        ▼
relabel the variant with the verified alignment
        │
        ▼
per-fragment LTS behavioural equivalence
        │
        ▼
edit script + fusion matrix + pairwise reports
```

The demo runs on the **Mini Hospital (cashier / FO / ED)** subset of the
`BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset` (68 BizAgi
XPDL files).

---

## Quick start

Requirements: Python 3.10+ (standard library only).

```bash
# Run the bundled dataset demo (writes reports/ as Markdown + JSON)
python3 -m bpmndiff demo

# Pairwise comparison
python3 -m bpmndiff reference.xpdl variant.xpdl

# Machine-readable output
python3 -m bpmndiff a.xpdl b.xpdl --format json --out diff.json

# Rebuild the synthetic 30-pair dataset (5 bases × k=1/2/4 × kept/new IDs)
python3 -m bpmndiff generate

# Score all four alignment modes against the generated ground truth
python3 -m bpmndiff evaluate

# Render the result figures (needs the optional viz extra)
pip install -e '.[viz]'
python3 -m bpmndiff visualize
```

Optional installation as a console command, in a local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/bpmndiff --help
```

The package has no runtime dependencies, so the virtual environment only keeps
the `bpmndiff` entry point and its metadata isolated from the system Python.
The analysis figures are the only optional install: `pip install -e '.[viz]'`
adds `pandas` and `matplotlib`; the comparison engine, generator, and evaluation
harness never import them.

The only optional dependency is a reachable OpenAI-compatible endpoint for
LLM adjudication of ambiguous label pairs (see below). Everything else is
offline and deterministic.

---

## Demo results

Run:

```bash
python3 -m bpmndiff demo --out reports
```

The scenarios are real process-family pairs from the Mini Hospital dataset:

| # | Scenario | Mode | Verdict | Trace equivalent |
|---|---|---|---|---|
| 1 | 51 old-patient registration → 52 general new-patient registration | A | semantic + behavioural change | no |
| 2 | 52 general → 53 corporate new-patient registration | A | semantic + behavioural change | no |
| 3 | 54 general → 55 corporate inpatient registration | A | semantic change only | **yes** |
| 4 | 58 general cashier → 59 down payment | A | semantic + behavioural change | no |

Highlights:

* **52 vs 53** — the corporate variant inserts one task
  (`Enters company informationk 1`) between *Enter the patient's address* and
  *Selects the register button*. The diff reports `INSERT` + two `INSERT_FLOW`
  operations, one `DELETE_FLOW`, one `RENAME`, and produces a counterexample
  trace that is accepted only by the variant.
* **54 vs 55** — apart from the semantic `general → corporate` change, the only
  textual difference is the typo `Displays → Risplays`. The lexical/semantic
  matcher classifies the typo as a synonym, so the trace language and branching
  bisimulation are **equivalent**.

Generated artefacts live in [`reports/`](reports/):
`demo_report.md`, `demo_summary.json`, and per-scenario `.md` and `.json`
files.

---

## Synthetic dataset & evaluation

`bpmndiff generate` builds **30 mutation pairs** from five diagrams
(`56`, `57`, `58`, `63`, `65` in the converted-XPDL dataset): `k = 1, 2, 4`
injected changes, each with element IDs kept and with every XML ID
regenerated. Every pair ships with a `change-v1` ground truth derived from the
generator's element-identity map, and each ground-truth record validates
against `schema/change-v1.json`.

Ground truth follows the edit-script contract in
[`docs/changes.md`](docs/changes.md): an inserted node is one `INSERT_NODE`
plus the new flows among matched nodes, while flows incident to a deleted node
are implied by its single `DELETE_NODE` and are not counted twice.

```bash
python3 -m bpmndiff generate   # dataset/synthetic/ (reference, variants, GT, manifest)
python3 -m bpmndiff evaluate   # results/pilot.csv + pilot_pairs.csv + summaries
```

Pilot result (operation-level Precision / Recall / F1 over all 30 pairs):

| Alignment mode | F1 (IDs kept) | F1 (IDs regenerated) | F1 (all) | FP | FN |
|---|---:|---:|---:|---:|---:|
| `id` | 1.000 | 0.075 | 0.197 | 687 | 30 |
| `name` | 0.248 | 0.244 | 0.246 | 596 | 18 |
| `structure` | 0.129 | 0.129 | 0.129 | 692 | 62 |
| `hybrid` | 1.000 | 1.000 | 1.000 | 0 | 0 |

`results/pilot.csv` breaks these numbers down per change type and per mode;
`results/error_analysis.md` describes the three most frequent failure
patterns with a concrete generated pair for each.

The headline is identifier churn: `id` alignment is exact while IDs survive and
collapses when a re-export renames every element. `hybrid` recovers the
injected edit script exactly on this pilot, which is expected because the
mutations stay within the signals hybrid combines. `name` alignment still
detects renames well (F1 `1.000` for `RENAME_NODE`, `NODE_TYPE_CHANGE`,
`MARKER_CHANGE`, `MOVE_LANE`) but produces flow-level false positives around
unnamed gateways, and `structure` alignment skips structurally symmetric
nodes and therefore misses both the node edit and its incident flows.

### Result figures

`bpmndiff visualize` reads `results/pilot.csv` and `results/pilot_pairs.csv`
and writes six PNGs plus a CSV to `results/figures/`:

| Figure | What it shows |
|---|---|
| `mode_overall.png` | Precision / Recall / F1 per alignment mode over all 30 pairs. |
| `type_mode_heatmap.png` | F1 per change type × alignment mode, with ground-truth support in the row labels. |
| `id_churn.png` | F1 before and after full ID regeneration, one line per mode. |
| `pair_mode_heatmap.png` | Per-pair F1 for every base variant, grouped by base diagram. |
| `pair_f1_distribution.png` | Box plot and individual points of per-pair F1 per mode. |
| `mode_correlation.png` | Pearson correlation between modes (per-pair F1 and predicted operation count). |
| `mode_correlation.csv` | The correlation matrices as data. |

They are a reporting layer only: no figure feeds back into the diff, and the
engine still runs on the standard library alone.

---

## CLI reference

```
bpmndiff FILES... [--format {text,json,markdown}]
         [--alignment-mode {id,name,structure,hybrid}]
         [--out PATH] [--process ID|NAME]
         [--max-states N] [--no-bisimulation] [--llm]
         [--threshold 0.45] [--fail-on-change]

bpmndiff demo [--dataset PATH] [--out DIR]

bpmndiff generate [--dataset DIR] [--out DIR] [--bases 56,57,58,63,65] [--seed SALT]
bpmndiff evaluate [--manifest PATH] [--out DIR]
                  [--modes id,name,structure,hybrid] [--bisimulation]
bpmndiff visualize [--results DIR] [--out DIR]
```

| Option | Meaning |
|---|---|
| *(no mode option)* | Pairwise comparison (Mode A) is the default. Exactly two files. |
| `--alignment-mode` | Select `id`, `name`, `structure`, or `hybrid` matching (default: `hybrid`). |
| `--process` | Select a workflow process by id or name inside a multi-process package. |
| `--max-states` | LTS exploration cap per model (default 20 000). |
| `--no-bisimulation` | Skip the partition-refinement check (faster). |
| `--llm` | Send only ambiguous label pairs to an OpenAI-compatible endpoint. |
| `--threshold` | Minimum label similarity for the lexical stage (default 0.45). |
| `--fail-on-change` | Exit with status 1 when trace equivalence is `False` (CI gate). |
| `generate --bases` | Comma-separated base diagram IDs (default: `56,57,58,63,65`). |
| `evaluate --manifest` | Synthetic dataset manifest (default: `dataset/synthetic/manifest.json`). |
| `evaluate --modes` | Alignment modes to score (default: all four). |
| `visualize --results` | Folder with `pilot.csv` and `pilot_pairs.csv` (default: `results`). |
| `visualize --out` | Figure output folder (default: `results/figures`). Requires the `[viz]` extra. |

Exit codes: `0` success, `1` behavioural change with `--fail-on-change`,
`2` parse/input error.

### Optional LLM fallback

Ambiguous pairs (similarity roughly 0.45–0.62) are marked `needs_review` by
default. To let an LLM adjudicate them:

```bash
export BPMNDIFF_LLM=1
export BPMNDIFF_LLM_URL=https://api.openai.com/v1/chat/completions
export BPMNDIFF_LLM_MODEL=gpt-4o-mini
export OPENAI_API_KEY=...
bpmndiff a.xpdl b.xpdl --llm
```

The response must be a JSON array with `label`, `confidence` and `reason` per
pair. Failures fall back to `needs_review`; the offline demo never calls the
network.

---

## What is implemented

### 1. Multi-format parsing and normalisation

* **XPDL 2.x** (`<Package>`) — `WorkflowProcess`, `Activity`/`Event`/`Route`,
  `Transition`, pools, lanes. BizAgi lanes are recovered from lane/activity
  `NodeGraphicsInfo` coordinates when `flowNodeRef`-style membership is absent.
* **BPMN 2.0** (`<definitions>`) — start/end/intermediate events, tasks,
  sub-processes (treated atomically), XOR/AND/OR gateways, sequence flows,
  lanes and participants.
* Format detection is based on the XML root, not the extension, so BPMN content
  in an `.xml` file is accepted. Layout/colour/coordinate data is discarded.
* BizAgi `Route` elements carry no `GatewayType`; they are normalised to XOR,
  matching BizAgi's default exclusive semantics. Explicit
  `GatewayType`/`parallelGateway`/`inclusiveGateway` values are respected.

### 2. Tiered alignment

1. **Exact** — normalised label equality (case, punctuation, whitespace).
2. **Lexical** — Jaro-Winkler plus sequence similarity for typos.
3. **Semantic (offline)** — canonical tokens, a domain synonym lexicon
   (`save/store`, `display/show`, `search/find`, `select/choose`, …) and
   token Dice overlap.
4. **Structural** — gateways and unnamed events are paired by matched
   neighbourhood context and degree.
5. **LLM fallback (optional)** — only ambiguous candidate pairs.

Alignment is selectable for ablation/testing through `--alignment-mode`:

* `id` matches shared BPMN/XML node IDs only.
* `name` matches named nodes by label similarity only.
* `structure` ignores IDs and labels while matching unique directed-topology
  fingerprints; ambiguous symmetric nodes are left unmatched.
* `hybrid` tries shared IDs first, then label similarity, structural context,
  and cross-family fallbacks.

Only pairwise comparison (Mode A) is supported. Use
`--alignment-mode structure` for a pairwise structural comparison.
Python callers select the same strategy with
`DiffOptions(alignment_config=AlignmentConfig(strategy="structure"))`; both
`AlignmentConfig` and `DiffOptions` are exported by `bpmndiff`. JSON results
record the selected strategy in `alignment_strategy`.

Pairs receive `identical`, `synonym`, `meaning_changed` or `unmatched`, a
confidence value and a `needs_review` flag. Domain contrasts
(`general/corporate`, `inpatient/outpatient`, `old/new`, …) deliberately cap
the score, so a business-variable change is not reported as a harmless rename.

### 3. SESE-style decomposition

Regions are derived from dominator/postdominator pairs and filtered by a
single-entry/single-exit boundary check. The result is a region tree with the
whole model as root. This is a practical approximation of an RPST: the
prototype only needs a reliable "smallest region containing the change" for
scoped behavioural checks. Fragment checks treat sinks as successful exits
(`open_ends=True`) because a fragment has no explicit end event of its own.

### 4. Behavioural engine (pure Python LTS)

* Token-passing semantics for start/end events, tasks, XOR, AND and OR
  gateways. Gateways and start events emit silent `tau` transitions.
* **Trace equivalence**: tau-closure → subset construction → product-automaton
  language comparison. A shortest counterexample trace and direction
  (`reference_only` / `variant_only`) are returned.
* **Branching bisimulation**: partition refinement over tau-closure
  signatures, in the spirit of the `ltscompare` algorithms (simplified for the
  prototype).
* Fragment-level checks run on the smallest affected regions and include
  inserted variant nodes that lie between mapped fragment nodes.
* Exploration is capped (`--max-states`) and reported as `INCONCLUSIVE`
  rather than silently claiming equivalence when truncated.

### 5. Edit script and fusion

Supported operations: `INSERT`, `DELETE`, `RENAME`, `CHANGE_TYPE`,
`CHANGE_GATEWAY_TYPE`, `RENAME_SWIMLANE`, `CHANGE_SWIMLANE`, plus
`INSERT_FLOW` / `DELETE_FLOW`. Swimlane renames are inferred from matched
nodes whose lane name changed; a `CHANGE_SWIMLANE` operation identifies a
matched node reassigned to a different lane. These organizational changes do
not alter control-flow equivalence.

The complete operation taxonomy — which operation detects which scope element
and compared aspect — is specified in
[`docs/taxonomy.md`](docs/taxonomy.md).

Per-element fusion follows the table in the specification:

| Alignment label | Behaviour | Verdict |
|---|---|---|
| `identical` / `synonym` | equivalent | non-behavioural rename |
| `identical` / `synonym` | not equivalent | behavioural change + counterexample |
| `meaning_changed` | either | semantic change (and behavioural if not equivalent) |
| `unmatched` | not equivalent | structural insert/delete |
| low confidence | any | **needs review** |

### 6. Pairwise comparison

The CLI compares exactly two process models and emits the edit script,
behavioural checks, affected fragments, and fusion verdict.

---

## Project layout

```
FP/
├── bpmndiff/
│   ├── model.py           # layout-free ProcessModel / Node / Edge
│   ├── parsers/           # XPDL + BPMN 2.0 loaders (stdlib ElementTree)
│   ├── alignment.py       # normalisation, similarity, pair/alignment model
│   ├── llm.py             # optional OpenAI-compatible adjudicator
│   ├── decomposition.py   # dominator/postdominator SESE-style regions
│   ├── lts.py             # token game, tau-closure, determinisation, traces
│   ├── bisimulation.py    # partition-refinement behavioural check
│   ├── diff.py            # edit script, fragment checks, fusion verdicts
│   ├── generator.py       # synthetic mutation dataset + change-v1 ground truth
│   ├── evaluation.py      # P/R/F1 per change type and alignment mode
│   ├── visualize.py       # optional pandas/matplotlib figures (the [viz] extra)
│   ├── report.py          # text / Markdown / JSON renderers
│   └── cli.py             # argparse CLI, dataset demo, generate/evaluate/visualize
├── tests/                 # unittest suite (no third-party test runner)
├── reports/               # generated demo artefacts
├── dataset/synthetic/     # generated reference/variant pairs + manifest
├── results/               # pilot.csv, pair metrics, summary, error analysis, figures/
├── docs/                  # source specification documents
└── pyproject.toml
```

Run the tests with:

```bash
python3 -m unittest discover -s tests -v
```

---

## Dataset notes

* Path: `BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/`.
* 68 XPDL 2.2 files from BizAgi Process Modeler, one diagram per functional
  requirement folder.
* Models contain pools/lanes, XOR routes, data-store references, and
  conditional transitions. Transition conditions are currently parsed but not
  evaluated (they do not affect the control-flow abstraction).
* The demo deliberately compares related functional variants
  (registration/registration, inpatient/inpatient, cashier/down-payment) so
  that alignment and behavioural differences are meaningful.

---

## Limitations and next steps

* **RPST approximation** — regions are dominator-based candidates, not a fully
  canonical RPST; nested/overlapping candidates can be reported. The smallest
  enclosing region used for scoped checks is reliable for the dataset sizes
  tested.
* **Gateway semantics** — untyped BizAgi routes default to XOR; AND/OR joins
  use a simplified token game (tokens are not synchronised at joins). This is
  sufficient for the small demo fragments but not a full BPMN execution
  semantics.
* **Conditions and data** — sequence-flow conditions, data objects and message
  flows are ignored; the comparison is control-flow only.
* **Sub-processes** are treated as atomic tasks; their interiors are not
  expanded.
* **Formats** — BPMN 2.0 and XPDL 2.x are supported. Visio `.vdx` and other
  vendor formats mentioned in the specification are not yet parsed.
* **Scale** — state exploration and alignment are polynomial-ish but the LTS
  is exponential in the worst case. Large models may return
  `INCONCLUSIVE`; raise `--max-states` or use `--no-bisimulation` for speed.
* **LLM adjudication** is opt-in and conservative; without it, ambiguous pairs
  remain explicitly flagged for manual review.
