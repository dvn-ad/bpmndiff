# Pair evaluation: 56 / k1_newids

| Field | Value |
|---|---|
| Base diagram | 56 |
| Variant | k1_newids |
| k | 1 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `56/reference.bpmn` |
| Variant path | `56/k1_newids.bpmn` |
| Ground truth | `56/k1_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| RENAME_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| RENAME_NODE | Id_1164e919-3f27-4d09-9a69-2a33a2e98847 |

## Diff report

### Pairwise comparison: reference.bpmn vs k1_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 11 | 11 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/reference.bpmn |
| Variant | bpmn | 11 | 11 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/56/k1_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 10 | 1 | 0 | 0 | 0 | 0 |

#### Edit script (1 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | RENAME_NODE | Enters the patient's name | "Enters the patient's name" -> "Enters the supplier's name" (synonym) | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (23 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R06 | 3 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**non_behavioral_rename**

- Element verdicts: `{'unchanged': 10, 'non_behavioral_rename': 1}`
- Operations: `{'RENAME_NODE': 1}`
- Needs review: False
