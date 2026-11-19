# Pair evaluation: 56 / k2_keep

| Field | Value |
|---|---|
| Base diagram | 56 |
| Variant | k2_keep |
| k | 2 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `56/reference.bpmn` |
| Variant path | `56/k2_keep.bpmn` |
| Ground truth | `56/k2_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 5 | 0 | 0 | 5 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
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
| INSERT_NODE | Mut_Node_1 |
| RENAME_NODE | Id_1164e919-3f27-4d09-9a69-2a33a2e98847 |
| DELETE_FLOW | Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 → Id_ffd9beac-13dd-4c0f-9c58-f3f304cf90f3 |
| INSERT_FLOW | Mut_Node_1 → Id_ffd9beac-13dd-4c0f-9c58-f3f304cf90f3 |
| INSERT_FLOW | Id_7fe42d3b-450f-4fbf-bbc1-02243994a598 → Mut_Node_1 |

## Diff report

### Pairwise comparison: reference.bpmn vs k2_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 11 | 11 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/reference.bpmn |
| Variant | bpmn | 12 | 12 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/k2_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 10 | 1 | 0 | 0 | 1 | 0 |

#### Edit script (5 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 1 | added task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters the patient's name | "Enters the patient's name" -> "Enters the supplier's name" (synonym) | no |
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

- Element verdicts: `{'non_behavioral_rename': 1, 'unchanged': 10, 'structural_change': 1}`
- Operations: `{'INSERT_NODE': 1, 'RENAME_NODE': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 2}`
- Needs review: False
