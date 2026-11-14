# Implementation Plan: BPMN Taxonomy & Scope Extension

## Architecture & Dependency Graph

```
[bpmndiff/model.py] (Extended Node, Edge, MessageFlow, DataElement)
        │
        ▼
[bpmndiff/parsers/__init__.py] (BPMN 2.0 & XPDL parsers)
        │
        ▼
[bpmndiff/diff.py] & [bpmndiff/alignment.py] (Taxonomy Change Detection)
        │
        ▼
[bpmndiff/report.py] & [bpmndiff/cli.py] (5-Category Reports & CLI)
        │
        ▼
[dataset/taxonomy_variants/*.bpmn] (BPMN Dataset Pairs & Demo Verification)
```

## Vertical Slices & Milestones

1. **Slice 1: Data Model Extensions** (`model.py`)
   - Add task types, event definitions, boundary event attributes (`attached_to`, `cancel_activity`), loop markers, gateway direction/default flows, `MessageFlow`, and `DataElement`.
2. **Slice 2: Parser Extraction** (`parsers/__init__.py`)
   - Extract extended BPMN 2.0 and XPDL XML constructs.
3. **Slice 3: Taxonomy Change Detection Engine** (`diff.py`, `alignment.py`)
   - Implement change operations across all 5 categories:
     - Steps: `INSERT_NODE`, `DELETE_NODE`, `RENAME_NODE` (synonym vs meaning changed), `NODE_TYPE_CHANGE`, `MARKER_CHANGE`, `BOUNDARY_CHANGE`.
     - Actors: `MOVE_LANE`, `RENAME_LANE`, `INSERT_LANE`, `DELETE_LANE`.
     - Sequence/Flow: `REORDER`, `GATEWAY_TYPE_CHANGE`, `INSERT_FLOW`, `DELETE_FLOW`, `FLOW_CONDITION_CHANGE`, `PARALLELIZE`, `SEQUENTIALIZE`.
     - Subprocess: `EXTRACT_SUBPROCESS`, `INLINE_SUBPROCESS`.
     - Data & Communication: `MESSAGE_FLOW_CHANGE`, `DATA_CHANGE`.
4. **Slice 4: Reporting and CLI** (`report.py`, `cli.py`)
   - Present taxonomy operations categorized cleanly in Text, Markdown, and JSON formats.
5. **Slice 5: BPMN Dataset Comparison Benchmark** (`dataset/taxonomy_variants/*.bpmn`)
   - Construct benchmark BPMN comparison models demonstrating each taxonomy category.
