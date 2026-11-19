# Pair evaluation: 58 / k4_keep

| Field | Value |
|---|---|
| Base diagram | 58 |
| Variant | k4_keep |
| k | 4 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `58/reference.bpmn` |
| Variant path | `58/k4_keep.bpmn` |
| Ground truth | `58/k4_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 4 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| RENAME_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MARKER_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MOVE_LANE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| MARKER_CHANGE | Id_0a7a1082-affb-4bc8-bfb1-91f073d72dde |
| RENAME_NODE | Id_259b95ad-426d-4d16-8f7b-6371212aaf57 |
| MOVE_LANE | Id_2235724b-6ca2-46d2-95a0-ab88837d316f |
| INSERT_FLOW | Id_ee3de915-745e-439b-bb67-c19333dfb907 → Id_6bc7314b-ee04-4f16-af27-1f79dcebf3d1 |

## Diff report

### Pairwise comparison: reference.bpmn vs k4_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 23 | 24 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/58/reference.bpmn |
| Variant | bpmn | 23 | 25 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/58/k4_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 22 | 1 | 0 | 0 | 0 | 0 |

#### Edit script (4 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | MARKER_CHANGE | Enter the medical record ID | marker: "none" -> "loop" | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays the query results | "Displays the query results" -> "Shows the query results" (synonym) | no |
| 2. Actors (lanes and pools) | MOVE_LANE | Displays it to the table | Displays it to the table: "System" -> "Cashier" | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Invisible Task -> <exclusive gateway (XOR)> | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (69 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R10 | 3 | EQUIVALENT | (empty trace) |
| R12 | 3 | EQUIVALENT | (empty trace) |
| R32 | 8 | skipped | (empty trace) |

#### Fusion verdict

**non_behavioral_swimlane_change**

- Element verdicts: `{'unchanged': 22, 'non_behavioral_rename': 1}`
- Operations: `{'MARKER_CHANGE': 1, 'RENAME_NODE': 1, 'MOVE_LANE': 1, 'INSERT_FLOW': 1}`
- Needs review: False
