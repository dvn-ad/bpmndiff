# Pair evaluation: 65 / k2_newids

| Field | Value |
|---|---|
| Base diagram | 65 |
| Variant | k2_newids |
| k | 2 |
| ID policy | newids |
| Scenario | new_ids |
| Alignment mode | hybrid |
| Reference | `65/reference.bpmn` |
| Variant path | `65/k2_newids.bpmn` |
| Ground truth | `65/k2_newids.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 2 | 0 | 0 | 2 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| GATEWAY_TYPE_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| FLOW_CONDITION_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| FLOW_CONDITION_CHANGE | Id_8a71f31d-70b3-48c5-bc2c-eea96af4d56f → Id_d877f453-58b4-46a1-aa8c-b53c44b2a526 |
| GATEWAY_TYPE_CHANGE | Id_6fe753e9-ea2f-4694-a19f-d7585b540d01 |

## Diff report

### Pairwise comparison: reference.bpmn vs k2_newids.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 22 | 26 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/65/reference.bpmn |
| Variant | bpmn | 22 | 26 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/65/k2_newids.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 22 | 0 | 0 | 0 | 0 | 0 |

#### Edit script (2 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 3. Sequence, flow, and branching | FLOW_CONDITION_CHANGE | <exclusive gateway (XOR)> -> Displays the message "data not found". | condition: "" -> "amount > 5" | no |
| 3. Sequence, flow, and branching | GATEWAY_TYPE_CHANGE | <exclusive gateway (XOR)> | XOR -> AND | no |

#### Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`

#### SESE fragments (58 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R10 | 4 | EQUIVALENT | (empty trace) |
| R21 | 7 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**unchanged**

- Element verdicts: `{'unchanged': 22}`
- Operations: `{'FLOW_CONDITION_CHANGE': 1, 'GATEWAY_TYPE_CHANGE': 1}`
- Needs review: False
