# Pair evaluation: 56 / k4_newids

| Field | Value |
|---|---|
| Base diagram | 56 |
| Variant | k4_newids |
| k | 4 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `56/reference.bpmn` |
| Variant path | `56/k4_newids.bpmn` |
| Ground truth | `56/k4_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 7 | 0 | 0 | 7 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| NODE_TYPE_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_LANE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
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
| INSERT_NODE | Id_c9d3bc63d456923e |
| NODE_TYPE_CHANGE | Id_61ffd82b-3da4-4f55-b5ea-a01fc381ca49 |
| RENAME_NODE | Id_1164e919-3f27-4d09-9a69-2a33a2e98847 |
| RENAME_LANE | FO |
| DELETE_FLOW | Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 → Id_ffd9beac-13dd-4c0f-9c58-f3f304cf90f3 |
| INSERT_FLOW | Id_c9d3bc63d456923e → Id_e93537424b0e138b |
| INSERT_FLOW | Id_b1e124fd4e53b5a8 → Id_c9d3bc63d456923e |

## Diff report

### Pairwise comparison: reference.bpmn vs k4_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 11 | 11 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/reference.bpmn |
| Variant | bpmn | 12 | 12 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/k4_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 10 | 1 | 0 | 0 | 1 | 0 |

#### Edit script (7 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 1 | added task | no |
| 1. Steps (tasks and events) | NODE_TYPE_CHANGE | Queries the Patient database, | abstract task -> user task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters the patient's name | "Enters the patient's name" -> "Enters the supplier's name" (synonym) | no |
| 2. Actors (lanes and pools) | RENAME_LANE | FO | "FO" -> "Front Office" | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Displays the query results to a table -> <exclusive gateway (XOR)> | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 1 -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays the query results to a table -> Adds verification step 1 | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (reference_only): `Wants Search for patient data information -> Displays the Search for patient data information form -> Enters the patient's name -> Selects a search button -> Queries the Patient database, -> Displays the query results to a table`
  - one model accepts this completed trace, the other does not

#### SESE fragments (23 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R06 | 3 | EQUIVALENT | (empty trace) |
| R11 | 5 | NOT EQUIVALENT | Queries the Patient database, -> Displays the query results to a table |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 9, 'behavioral_change': 1, 'non_behavioral_rename': 1, 'structural_change': 1}`
- Operations: `{'INSERT_NODE': 1, 'NODE_TYPE_CHANGE': 1, 'RENAME_NODE': 1, 'RENAME_LANE': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 2}`
- Needs review: False
