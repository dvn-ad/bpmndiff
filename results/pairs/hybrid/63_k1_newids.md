# Pair evaluation: 63 / k1_newids

| Field | Value |
|---|---|
| Base diagram | 63 |
| Variant | k1_newids |
| k | 1 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `63/reference.bpmn` |
| Variant path | `63/k1_newids.bpmn` |
| Ground truth | `63/k1_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| NODE_TYPE_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| NODE_TYPE_CHANGE | Id_082521f7-2373-493e-b116-ed46f8443646 |

## Diff report

### Pairwise comparison: reference.bpmn vs k1_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 13 | 13 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/reference.bpmn |
| Variant | bpmn | 13 | 13 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/k1_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 13 | 0 | 0 | 0 | 0 | 0 |

#### Edit script (1 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | NODE_TYPE_CHANGE | Queries database | abstract task -> user task | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (46 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R07 | 3 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**unchanged**

- Element verdicts: `{'unchanged': 13}`
- Operations: `{'NODE_TYPE_CHANGE': 1}`
- Needs review: False
