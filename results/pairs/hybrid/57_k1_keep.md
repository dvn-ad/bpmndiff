# Pair evaluation: 57 / k1_keep

| Field | Value |
|---|---|
| Base diagram | 57 |
| Variant | k1_keep |
| k | 1 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `57/reference.bpmn` |
| Variant path | `57/k1_keep.bpmn` |
| Ground truth | `57/k1_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 4 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_FLOW | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| INSERT_NODE | Mut_Node_2 |
| DELETE_FLOW | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 → Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 |
| INSERT_FLOW | Mut_Node_2 → Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 |
| INSERT_FLOW | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 → Mut_Node_2 |

## Diff report

### Pairwise comparison: reference.bpmn vs k1_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 8 | 7 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/reference.bpmn |
| Variant | bpmn | 9 | 8 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/k1_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 8 | 0 | 0 | 0 | 1 | 0 |

#### Edit script (4 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 2 | added task | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Queries to the Rooms database -> Displays the query results to a table | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 2 -> Displays the query results to a table | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Queries to the Rooms database -> Adds verification step 2 | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants Looking for room data -> Reads the Room database -> Displays the Looking for room data form -> Selects the room category -> Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table`
  - only this model can execute the differing task and still complete

#### SESE fragments (28 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R00 | 2 | EQUIVALENT | (empty trace) |
| R02 | 2 | NOT EQUIVALENT | Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 8, 'structural_change': 1}`
- Operations: `{'INSERT_NODE': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 2}`
- Needs review: False
