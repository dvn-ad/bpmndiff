# Change taxonomy and output contract

This document defines the canonical change vocabulary and the versioned
per-operation output contract. The machine-readable contract is
[`schema/change-v1.json`](../schema/change-v1.json).

## Canonical taxonomy

Every `change.type` is one of the operation types below. `legacy_type` and the
top-level compatibility fields preserve the previous `operations` format.

| Canonical type | Legacy type | Category | Element | Meaning |
| --- | --- | ---: | --- | --- |
| `INSERT_NODE` | `INSERT` | 1 | node | A task, event, or gateway exists only in the variant. |
| `DELETE_NODE` | `DELETE` | 1 | node | A task, event, or gateway exists only in the reference. |
| `RENAME_NODE` | `RENAME` | 1 | node | A matched node's label changed; `subtype` is `synonym` or `meaning_changed`. |
| `NODE_TYPE_CHANGE` | `CHANGE_TYPE` | 1 | node | A matched node's BPMN kind, task type, or event definition changed. |
| `MARKER_CHANGE` | `MARKER_CHANGE` | 1 | node | A loop or multi-instance marker changed. |
| `BOUNDARY_CHANGE` | `BOUNDARY_CHANGE` | 1 | boundary_event | Boundary attachment or interrupting behavior changed. |
| `MOVE_LANE` | `CHANGE_SWIMLANE` | 2 | swimlane | A matched node moved to another lane. |
| `RENAME_LANE` | `RENAME_SWIMLANE` | 2 | swimlane | A lane label changed. |
| `INSERT_LANE` | `INSERT_LANE` | 2 | swimlane | A lane exists only in the variant. |
| `DELETE_LANE` | `DELETE_LANE` | 2 | swimlane | A lane exists only in the reference. |
| `GATEWAY_TYPE_CHANGE` | `CHANGE_GATEWAY_TYPE` | 3 | gateway | A matched gateway's kind changed. |
| `INSERT_FLOW` | `INSERT_FLOW` | 3 | flow | A sequence flow exists only in the variant. |
| `DELETE_FLOW` | `DELETE_FLOW` | 3 | flow | A sequence flow exists only in the reference. |
| `FLOW_CONDITION_CHANGE` | `FLOW_CONDITION_CHANGE` | 3 | flow | A flow condition or default-flow flag changed. |
| `REORDER` | `REORDER` | 3 | node | The relative execution order of matched nodes was inverted. |
| `PARALLELIZE` | `PARALLELIZE` | 3 | node | Sequential activities became parallel. |
| `SEQUENTIALIZE` | `SEQUENTIALIZE` | 3 | node | Parallel activities became sequential. |
| `EXTRACT_SUBPROCESS` | `EXTRACT_SUBPROCESS` | 4 | subprocess | Root activities were moved into a subprocess. |
| `INLINE_SUBPROCESS` | `INLINE_SUBPROCESS` | 4 | subprocess | Subprocess activities were moved into the root process. |
| `MESSAGE_FLOW_CHANGE` | `MESSAGE_FLOW_CHANGE` | 5 | message_flow | A cross-pool message flow was added or removed. |
| `DATA_CHANGE` | `DATA_CHANGE` | 5 | data | A data object/store/input/output was added or removed. |

Category IDs are stable: 1 steps, 2 actors, 3 sequence and branching,
4 subprocess structure, and 5 data and communication. Alignment labels are
`identical`, `synonym`, `meaning_changed`, or `unmatched`. Confidence is
`high`, `medium`, or `low`.

## Per-change envelope

Each entry in `operations` uses the following two layers:

```json
{
  "schema_version": "change-v1",
  "change": {
    "type": "RENAME_NODE",
    "legacy_type": "RENAME",
    "category": 1,
    "category_name": "Steps (tasks and events)",
    "element": "node",
    "before": {"id": "task-a", "name": "Save form"},
    "after": {"id": "task-b", "name": "Store form"},
    "detail": "\"Save form\" -> \"Store form\" (synonym)",
    "label": "synonym",
    "subtype": "synonym",
    "is_synonym": true,
    "score": 0.94,
    "confidence": "high",
    "needs_review": false
  },
  "evidence": {
    "alignment": [
      {
        "reference_node_id": "task-a",
        "variant_node_id": "task-b",
        "label": "synonym",
        "score": 0.94,
        "reason": "canonical token equivalence",
        "confidence": "high",
        "needs_review": false
      }
    ],
    "structural_context": [],
    "observations": [
      {"source": "alignment", "description": "canonical token equivalence"}
    ]
  }
}
```

The actual top-level record also retains the prior flat fields (`op`,
`legacy_op`, `before`, `after`, and others) as compatibility mirrors. New
consumers should read `change` and `evidence`; the invariant checker verifies
that any mirrored fields agree.

`evidence.alignment` contains the relevant alignment score, label, confidence,
and rationale. `evidence.structural_context` records the related node IDs,
degrees, and already-matched neighbors when available. `observations` records
the graph, attribute, lane, or data facts used for the operation. Geometry is
not emitted: the current parsers discard BPMN DI coordinates.

## Runtime invariants

Every completed comparison validates each change envelope against
`schema/change-v1.json` and checks that:

1. each node in both models occurs exactly once in the alignment;
2. forward/reverse alignment maps agree and are one-to-one;
3. every unmatched node has exactly one corresponding `DELETE_NODE` or
   `INSERT_NODE`, and those nodes are not also matched;
4. matched-node operations point to the exact aligned pair; and
5. compatibility fields agree with their canonical `change` fields.

Violations raise `ComparisonInvariantError`; they are not silently omitted.
