# Specification: BPMN/XPDL Change Taxonomy and Extended Comparison

## Assumptions
1. We preserve backward compatibility: existing CLI commands, outputs, and existing tests continue to pass or are cleanly upgraded to the new taxonomy.
2. The core workflow and alignment algorithm in `bpmndiff` remains lightweight and dependency-free (standard library only), with optional LLM adjudication if configured.
3. The dataset comparison pairs will be built in **BPMN 2.0 XML** format (`.bpmn`), derived from or inspired by real processes in `BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset` and placed in `dataset/taxonomy_variants/`.
4. **Offline Synonym Detection**: Without LLM, `RENAME_NODE` determines whether a change is a synonym or meaning change via deterministic heuristics:
   - Canonical token reduction via built-in synonym lookup dictionary (`_SYNONYMS`) and domain phrase mappings (`_PHRASES`).
   - Suffix stemming (`basic_stem`) and stopword removal.
   - Contrast/antonym group checks (`_CONTRAST_GROUPS`): if mutually exclusive terms (e.g. `general` vs `corporate`, `inpatient` vs `outpatient`, `old` vs `new`) are substituted, it is flagged as `meaning_changed` (not synonym).
   - Multi-metric string similarity (token Dice, Jaro-Winkler, Levenshtein ratio) on canonicalized tokens: if canonical tokens match or have high synonym overlap, it is classified as `synonym` (`is_synonym=True`); otherwise `meaning_changed` (`is_synonym=False`).
5. Both BPMN 2.0 XML and XPDL 2.x XML formats will support the extended attributes (markers, boundary events, task types, event definitions, data objects, message flows, subprocesses) to the extent expressed in their respective schemas.

---

## 1. Objective
Implement the complete BPMN comparison scope and change taxonomy defined in `future.md`:
1. **Extended Element Scope**:
   - **Events**: Start, Intermediate (catch/throw), End, Boundary events (attached activity, interrupting/non-interrupting, event definitions).
   - **Activities**: Specific task types (user, service, manual, script, send, receive, business rule), Sub-processes and Call Activities, Loop and Multi-instance markers.
   - **Gateways**: XOR, OR, AND, Event-based, Complex, gateway direction (split/join), default flows.
   - **Connecting Objects**: Sequence flows (conditions, default flow), Message flows (inter-pool).
   - **Swimlanes**: Pools, Lanes, nested lanes.
   - **Data**: Data objects, Data stores, Data input/output, associations.
2. **BPMNDiff Change Taxonomy**:
   - Detect and classify 5 categories of operations:
     1. Steps: `INSERT_NODE`, `DELETE_NODE`, `RENAME_NODE` (synonym vs meaning change), `NODE_TYPE_CHANGE`, `MARKER_CHANGE`, `BOUNDARY_CHANGE`.
     2. Actors: `MOVE_LANE`, `RENAME_LANE`, `INSERT_LANE`, `DELETE_LANE`.
     3. Sequence, Flow, & Branching: `REORDER`, `GATEWAY_TYPE_CHANGE`, `INSERT_FLOW`, `DELETE_FLOW`, `FLOW_CONDITION_CHANGE`, `PARALLELIZE`, `SEQUENTIALIZE`.
     4. Sub-process Structure: `EXTRACT_SUBPROCESS`, `INLINE_SUBPROCESS`.
     5. Data & Cross-Pool Communication: `MESSAGE_FLOW_CHANGE`, `DATA_CHANGE`.
3. **Dataset & Demonstration**:
   - Adapt and modify processes from `BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset` into benchmark comparison pairs that trigger every taxonomy code.
   - Update CLI (`bpmndiff demo` and general diff) and report generators (text, JSON, markdown) to display the taxonomy results clearly.

---

## 2. Tech Stack & Commands
- **Language**: Python 3.10+ (current environment is Python 3.14).
- **Dependencies**: Standard library only (`xml.etree.ElementTree`, `difflib`, `dataclasses`, `argparse`, `typing`, `collections`).
- **Commands**:
  - Run Tests: `python3 -m unittest discover tests`
  - Run CLI: `python3 -m bpmndiff <model1> <model2>`
  - Run Taxonomy Demo: `python3 -m bpmndiff demo`

---

## 3. Project Structure
```text
bpmndiff/
  model.py           → Extended ProcessModel, Node, Edge, MessageFlow, DataObject, DataAssociation
  parsers/
    __init__.py      → Extended XPDL and BPMN parsers extracting all attributes
  alignment.py       → Multi-tiered alignment including new node kinds and attributes
  diff.py            → Taxonomy detection engine implementing all 5 categories
  report.py          → Text, JSON, and Markdown renderers grouping by taxonomy categories
  cli.py             → CLI and demo scenarios
dataset/
  taxonomy_variants/ → Comparison pairs based on XPDL/BPMN dataset demonstrating taxonomy changes
tests/
  test_core.py       → Unit tests for models and behavioural comparison
  test_parsers.py    → Tests for parsing extended BPMN and XPDL features
  test_taxonomy.py   → Comprehensive unit tests verifying each taxonomy change detection
  test_cli.py        → CLI and demo execution tests
```

---

## 4. Code Style & Conventions
- Pure Python standard library, strictly typed with type annotations.
- Immutability where practical, dataclasses with sensible defaults.
- Clean functional separation: Parsing -> Normalised Model -> Alignment -> Taxonomy Diff -> Behavioral Analysis -> Report Rendering.
- Example:
```python
@dataclass
class Node:
    id: str
    name: str = ""
    kind: str = "task"           # task, start, end, event, xor, and, or, subprocess, etc.
    task_type: str = "abstract"  # user, service, manual, script, send, receive, business_rule
    event_definition: str = "none" # timer, message, error, signal, conditional, terminate, etc.
    attached_to: str | None = None # For boundary events: activity id
    cancel_activity: bool = True   # For boundary events: interrupting vs non-interrupting
    marker: str = "none"           # none, loop, multi_instance_parallel, multi_instance_sequential
    lane: str = ""
    pool: str = ""
    submodel_node_ids: list[str] = field(default_factory=list)
```

---

## 5. Testing Strategy
- **Unit Tests (`tests/test_taxonomy.py`)**:
  - One or more targeted test cases for every taxonomy change code:
    - `INSERT_NODE`, `DELETE_NODE`, `RENAME_NODE` (distinguishing synonym vs meaning changed).
    - `NODE_TYPE_CHANGE` (e.g. user task -> service task, none event -> timer event).
    - `MARKER_CHANGE` (none -> loop / multi-instance).
    - `BOUNDARY_CHANGE` (attached activity moved or interrupting toggle).
    - `MOVE_LANE`, `RENAME_LANE`, `INSERT_LANE`, `DELETE_LANE`.
    - `REORDER` (element order swapped).
    - `GATEWAY_TYPE_CHANGE` (XOR -> AND / OR).
    - `INSERT_FLOW`, `DELETE_FLOW`, `FLOW_CONDITION_CHANGE`.
    - `PARALLELIZE`, `SEQUENTIALIZE`.
    - `EXTRACT_SUBPROCESS`, `INLINE_SUBPROCESS`.
    - `MESSAGE_FLOW_CHANGE`, `DATA_CHANGE`.
- **Parser Tests (`tests/test_parsers.py`)**:
  - Verify extraction of boundary events, task types, event definitions, loop markers, subprocesses, data objects, and message flows in both BPMN and XPDL.
- **Regression Tests (`tests/test_core.py`, `tests/test_cli.py`)**:
  - Ensure all 21 existing unit tests continue to pass.
- **Demo Verification**:
  - Ensure `python3 -m bpmndiff demo` runs cleanly and reports taxonomy categories.

---

## 6. Boundaries
- **Always**:
  - Run full test suite before completing.
  - Maintain zero third-party runtime dependency requirement.
  - Preserve backward compatibility for existing diff outputs.
- **Ask First**:
  - Modifying the existing files in `BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset` directly (we should create modified variant files in a dedicated comparison subfolder, preserving originals).
- **Never**:
  - Silently drop attributes during parsing.
  - Suppress test failures or lower verification bars.

---

## 7. Success Criteria
1. All 5 change taxonomy categories from `future.md` (and their respective operations) are formally represented and detected by `bpmndiff`.
2. Extended aspects for Events, Activities, Gateways, Connecting objects, Swimlanes, and Data are parsed from BPMN 2.0 and XPDL 2.x models.
3. Test suite covers 100% of the taxonomy change types with passing tests.
4. Evaluation dataset of modified XPDL/BPMN models demonstrates all comparison capabilities.
5. `python3 -m unittest discover tests` and `python3 -m bpmndiff demo` execute successfully.

---

## 8. Open Questions & Assumptions for Review
1. **Dataset Location**: We propose storing modified comparison pairs in `dataset/taxonomy_variants/` derived from the XPDL dataset (e.g. taking `Diagram 1.xpdl` from user management, login, patient registration, cashier, etc. and creating `_v2` variations), keeping the original XPDL Dataset intact. Does that match your preference?
2. **Operation Code Naming**: We will update operation codes to align exactly with `future.md` (`INSERT_NODE`, `DELETE_NODE`, `RENAME_NODE`, `MOVE_LANE`, `RENAME_LANE`, `NODE_TYPE_CHANGE`, etc.), while providing backward-compatible aliasing in report renderers if needed.
