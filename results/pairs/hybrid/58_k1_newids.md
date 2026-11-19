# Pair evaluation: 58 / k1_newids

| Field | Value |
|---|---|
| Base diagram | 58 |
| Variant | k1_newids |
| k | 1 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `58/reference.bpmn` |
| Variant path | `58/k1_newids.bpmn` |
| Ground truth | `58/k1_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| MARKER_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| MARKER_CHANGE | Id_0a7a1082-affb-4bc8-bfb1-91f073d72dde |

## Diff report

### Pairwise comparison: reference.bpmn vs k1_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 23 | 24 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/58/reference.bpmn |
| Variant | bpmn | 23 | 24 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/58/k1_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 23 | 0 | 0 | 0 | 0 | 0 |

#### Edit script (1 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | MARKER_CHANGE | Enter the medical record ID | marker: "none" -> "loop" | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (69 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R10 | 3 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**unchanged**

- Element verdicts: `{'unchanged': 23}`
- Operations: `{'MARKER_CHANGE': 1}`
- Needs review: False
