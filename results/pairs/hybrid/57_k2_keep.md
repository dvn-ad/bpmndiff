# Pair evaluation: 57 / k2_keep

| Field | Value |
|---|---|
| Base diagram | 57 |
| Variant | k2_keep |
| k | 2 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `57/reference.bpmn` |
| Variant path | `57/k2_keep.bpmn` |
| Ground truth | `57/k2_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 6 | 0 | 0 | 6 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_FLOW | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| DELETE_NODE | Id_1164e919-3f27-4d09-9a69-2a33a2e98847 |
| INSERT_NODE | Mut_Node_2 |
| DELETE_FLOW | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 → Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 |
| INSERT_FLOW | Mut_Node_2 → Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 |
| INSERT_FLOW | Id_b95890b5-92e4-432a-b709-a96b40733427 → Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 |
| INSERT_FLOW | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 → Mut_Node_2 |

## Diff report

### Pairwise comparison: reference.bpmn vs k2_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 8 | 7 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/reference.bpmn |
| Variant | bpmn | 8 | 7 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/k2_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 7 | 0 | 0 | 1 | 1 | 0 |

#### Edit script (6 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Selects the room category | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 2 | added task | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Queries to the Rooms database -> Displays the query results to a table | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 2 -> Displays the query results to a table | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays the Looking for room data form -> Queries to the Rooms database | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Queries to the Rooms database -> Adds verification step 2 | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants Looking for room data -> Reads the Room database -> Displays the Looking for room data form -> Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table`
  - only this model can execute the differing task and still complete

#### SESE fragments (28 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R02 | 2 | NOT EQUIVALENT | Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table |
| R08 | 3 | NOT EQUIVALENT | Displays the Looking for room data form -> Queries to the Rooms database |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 7, 'structural_change': 2}`
- Operations: `{'DELETE_NODE': 1, 'INSERT_NODE': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 3}`
- Needs review: False
