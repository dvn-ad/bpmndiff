# Pair evaluation: 63 / k2_keep

| Field | Value |
|---|---|
| Base diagram | 63 |
| Variant | k2_keep |
| k | 2 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `63/reference.bpmn` |
| Variant path | `63/k2_keep.bpmn` |
| Ground truth | `63/k2_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| RENAME_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
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
| RENAME_NODE | Id_0a7a1082-affb-4bc8-bfb1-91f073d72dde |

## Diff report

### Pairwise comparison: reference.bpmn vs k2_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 13 | 13 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/reference.bpmn |
| Variant | bpmn | 13 | 13 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/k2_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 12 | 1 | 0 | 0 | 0 | 0 |

#### Edit script (2 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | NODE_TYPE_CHANGE | Queries database | abstract task -> user task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters the medical record ID number | "Enters the medical record ID number" -> "Enters the financial record ID number" (synonym) | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (46 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R07 | 3 | EQUIVALENT | (empty trace) |
| R08 | 3 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**non_behavioral_rename**

- Element verdicts: `{'unchanged': 12, 'non_behavioral_rename': 1}`
- Operations: `{'NODE_TYPE_CHANGE': 1, 'RENAME_NODE': 1}`
- Needs review: False
