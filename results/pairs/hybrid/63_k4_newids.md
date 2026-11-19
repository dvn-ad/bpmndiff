# Pair evaluation: 63 / k4_newids

| Field | Value |
|---|---|
| Base diagram | 63 |
| Variant | k4_newids |
| k | 4 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `63/reference.bpmn` |
| Variant path | `63/k4_newids.bpmn` |
| Ground truth | `63/k4_newids.groundtruth.json` |

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
| GATEWAY_TYPE_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
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
| INSERT_NODE | Id_7dce96339c8078b2 |
| NODE_TYPE_CHANGE | Id_082521f7-2373-493e-b116-ed46f8443646 |
| RENAME_NODE | Id_0a7a1082-affb-4bc8-bfb1-91f073d72dde |
| DELETE_FLOW | Id_082521f7-2373-493e-b116-ed46f8443646 → Id_b95890b5-92e4-432a-b709-a96b40733427 |
| GATEWAY_TYPE_CHANGE | Id_7a3f28d2-8c48-4551-9672-ee6753bda510 |
| INSERT_FLOW | Id_7dce96339c8078b2 → Id_742ae18dab9f7ea9 |
| INSERT_FLOW | Id_6ea247b846cf1b9c → Id_7dce96339c8078b2 |

## Diff report

### Pairwise comparison: reference.bpmn vs k4_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 13 | 13 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/reference.bpmn |
| Variant | bpmn | 14 | 14 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/63/k4_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 12 | 1 | 0 | 0 | 1 | 0 |

#### Edit script (7 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 4 | added task | no |
| 1. Steps (tasks and events) | NODE_TYPE_CHANGE | Queries database | abstract task -> user task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters the medical record ID number | "Enters the medical record ID number" -> "Enters the financial record ID number" (synonym) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Queries database -> Displays the query result | flow removed (1x) | no |
| 3. Sequence, flow, and branching | GATEWAY_TYPE_CHANGE | <exclusive gateway (XOR)> | XOR -> AND | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 4 -> Displays the query result | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Queries database -> Adds verification step 4 | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to Update Patient Information -> Displays form of Updates Patient Information -> Enters the medical record ID number -> Queries database -> Adds verification step 4 -> Displays the query result -> Enter an update information -> Select an update button -> Invisible Task`
  - only this model can execute the differing task and still complete

#### SESE fragments (46 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R07 | 3 | NOT EQUIVALENT | Enters the medical record ID number -> Queries database -> Adds verification step 4 -> Displays the query result |
| R08 | 3 | EQUIVALENT | (empty trace) |
| R23 | 5 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 11, 'behavioral_change': 1, 'non_behavioral_rename': 1, 'structural_change': 1}`
- Operations: `{'INSERT_NODE': 1, 'NODE_TYPE_CHANGE': 1, 'RENAME_NODE': 1, 'DELETE_FLOW': 1, 'GATEWAY_TYPE_CHANGE': 1, 'INSERT_FLOW': 2}`
- Needs review: False
