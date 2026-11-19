# Pair evaluation: 57 / k4_newids

| Field | Value |
|---|---|
| Base diagram | 57 |
| Variant | k4_newids |
| k | 4 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `57/reference.bpmn` |
| Variant path | `57/k4_newids.bpmn` |
| Ground truth | `57/k4_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 8 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_FLOW | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| FLOW_CONDITION_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DATA_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| DELETE_NODE | Id_1164e919-3f27-4d09-9a69-2a33a2e98847 |
| INSERT_NODE | Id_013d7c2e46c25ecf |
| DELETE_FLOW | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 → Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 |
| FLOW_CONDITION_CHANGE | Id_8d8ff637-b07c-4252-a38a-d6864657c6a7 → Id_baf5345e-3bb0-4235-bb5f-c58fa8217646 |
| INSERT_FLOW | Id_013d7c2e46c25ecf → Id_e52e896036b105cf |
| INSERT_FLOW | Id_623aa990ac80758e → Id_d5961c1f5718fbde |
| INSERT_FLOW | Id_d5961c1f5718fbde → Id_013d7c2e46c25ecf |
| DATA_CHANGE | Audit log 2 |

## Diff report

### Pairwise comparison: reference.bpmn vs k4_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 8 | 7 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/reference.bpmn |
| Variant | bpmn | 8 | 7 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/57/k4_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 7 | 0 | 0 | 1 | 1 | 0 |

#### Edit script (8 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Selects the room category | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 2 | added task | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Queries to the Rooms database -> Displays the query results to a table | flow removed (1x) | no |
| 3. Sequence, flow, and branching | FLOW_CONDITION_CHANGE | Wants Looking for room data -> Reads the Room database | condition: "" -> "amount > 2" | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 2 -> Displays the query results to a table | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays the Looking for room data form -> Queries to the Rooms database | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Queries to the Rooms database -> Adds verification step 2 | flow added (1x) | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Audit log 2 | data object added: "Audit log 2" | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants Looking for room data -> Reads the Room database -> Displays the Looking for room data form -> Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table`
  - only this model can execute the differing task and still complete

#### SESE fragments (28 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R02 | 2 | NOT EQUIVALENT | Queries to the Rooms database -> Adds verification step 2 -> Displays the query results to a table |
| R05 | 2 | EQUIVALENT | (empty trace) |
| R08 | 3 | NOT EQUIVALENT | Displays the Looking for room data form -> Queries to the Rooms database |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 7, 'structural_change': 2}`
- Operations: `{'DELETE_NODE': 1, 'INSERT_NODE': 1, 'DELETE_FLOW': 1, 'FLOW_CONDITION_CHANGE': 1, 'INSERT_FLOW': 3, 'DATA_CHANGE': 1}`
- Needs review: False
