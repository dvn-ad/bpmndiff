# Tasks

- [x] Task 1: Extend Process Model with Full Element Scope
  - Acceptance: `Node`, `Edge`, `MessageFlow`, and `DataElement` support all aspects in `future.md` (task types, event definitions, boundary events, markers, directions, default flows, message flows, data stores/objects).
  - Verify: Unit test in `tests/test_taxonomy.py`.
  - Files: `bpmndiff/model.py`, `tests/test_taxonomy.py`

- [x] Task 2: Extend BPMN and XPDL Parsers
  - Acceptance: Parsers extract boundary events, task types, event definitions, loop markers, subprocesses, gateway directions, default flows, message flows, and data stores/objects.
  - Verify: `python3 -m unittest discover tests`.
  - Files: `bpmndiff/parsers/__init__.py`, `tests/test_parsers.py`

- [x] Task 3: Implement 5-Category Taxonomy Change Detection in Diff Engine
  - Acceptance: `diff.py` detects all 5 categories (`INSERT_NODE`, `DELETE_NODE`, `RENAME_NODE` [with synonym/meaning_change flags], `NODE_TYPE_CHANGE`, `MARKER_CHANGE`, `BOUNDARY_CHANGE`, `MOVE_LANE`, `RENAME_LANE`, `INSERT_LANE`, `DELETE_LANE`, `REORDER`, `GATEWAY_TYPE_CHANGE`, `INSERT_FLOW`, `DELETE_FLOW`, `FLOW_CONDITION_CHANGE`, `PARALLELIZE`, `SEQUENTIALIZE`, `EXTRACT_SUBPROCESS`, `INLINE_SUBPROCESS`, `MESSAGE_FLOW_CHANGE`, `DATA_CHANGE`).
  - Verify: `python3 -m unittest tests/test_taxonomy.py`.
  - Files: `bpmndiff/diff.py`, `bpmndiff/alignment.py`, `tests/test_taxonomy.py`

- [x] Task 4: Update Reporting and CLI
  - Acceptance: Text, Markdown, and JSON reports group and display changes under the 5 taxonomy categories. CLI commands work seamlessly.
  - Verify: `python3 -m unittest discover tests`.
  - Files: `bpmndiff/report.py`, `bpmndiff/cli.py`

- [x] Task 5: Build BPMN Dataset Comparison Suite & Verify End-to-End
  - Acceptance: Benchmark comparison models created in `dataset/taxonomy_variants/` covering all taxonomy categories; end-to-end demo and diff runs successfully.
  - Verify: `python3 -m bpmndiff dataset/taxonomy_variants/...` and `python3 -m bpmndiff demo`.
  - Files: `dataset/taxonomy_variants/*.bpmn`, `bpmndiff/cli.py`
