# Pair evaluation: 65 / k4_keep

| Field | Value |
|---|---|
| Base diagram | 65 |
| Variant | k4_keep |
| k | 4 |
| ID policy | keep |
| Scenario | keep_ids |
| Alignment mode | hybrid |
| Reference | `65/reference.bpmn` |
| Variant path | `65/k4_keep.bpmn` |
| Ground truth | `65/k4_keep.groundtruth.json` |

## Metrics

| TP | FP | FN | Support | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| 8 | 0 | 0 | 8 | 1.000 | 1.000 | 1.000 |

### Per change type

| Change type | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| INSERT_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_NODE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| GATEWAY_TYPE_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_FLOW | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| FLOW_CONDITION_CHANGE | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Mismatches

### False positives

_None._

### False negatives

_None._

## Ground truth operations

| Change type | Identity |
|---|---|
| DELETE_NODE | Id_082521f7-2373-493e-b116-ed46f8443646 |
| INSERT_NODE | Mut_Node_5 |
| DELETE_FLOW | Id_778fd50a-2f20-4db3-9a8b-ea705dc632c1 → Id_c4d65e81-c03c-4448-b16e-30e66f1889ea |
| FLOW_CONDITION_CHANGE | Id_8a71f31d-70b3-48c5-bc2c-eea96af4d56f → Id_d877f453-58b4-46a1-aa8c-b53c44b2a526 |
| GATEWAY_TYPE_CHANGE | Id_6fe753e9-ea2f-4694-a19f-d7585b540d01 |
| INSERT_FLOW | Mut_Node_5 → Id_c4d65e81-c03c-4448-b16e-30e66f1889ea |
| INSERT_FLOW | Id_0a7a1082-affb-4bc8-bfb1-91f073d72dde → Id_8a71f31d-70b3-48c5-bc2c-eea96af4d56f |
| INSERT_FLOW | Id_778fd50a-2f20-4db3-9a8b-ea705dc632c1 → Mut_Node_5 |

## Diff report

### Pairwise comparison: reference.bpmn vs k4_keep.bpmn

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 22 | 26 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/65/reference.bpmn |
| Variant | bpmn | 22 | 26 | /home/mendoan/Projects/bpmndiff/dataset/synthetic/65/k4_keep.bpmn |

#### Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 21 | 0 | 0 | 1 | 1 | 0 |

#### Edit script (8 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Sreads the Registration database | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Adds verification step 5 | added task | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Selects the condition button -> <exclusive gateway (XOR)> | flow removed (1x) | no |
| 3. Sequence, flow, and branching | FLOW_CONDITION_CHANGE | <exclusive gateway (XOR)> -> Displays the message "data not found". | condition: "" -> "amount > 5" | no |
| 3. Sequence, flow, and branching | GATEWAY_TYPE_CHANGE | <exclusive gateway (XOR)> | XOR -> AND | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Adds verification step 5 -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Enters register number of a patient -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Selects the condition button -> Adds verification step 5 | flow added (1x) | no |

#### Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to create an Emergency room Triage -> Displays the Emergency room Triage form -> Enters register number of a patient -> Displays patient information -> Selects the condition button -> Adds verification step 5 -> Bad -> Selects the save button -> Invisible Task`
  - only this model can execute the differing task and still complete

#### SESE fragments (58 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R15 | 5 | EQUIVALENT | (empty trace) |
| R17 | 6 | NOT EQUIVALENT | Enters register number of a patient -> Displays patient information |
| R20 | 7 | NOT EQUIVALENT | Selects the condition button -> Adds verification step 5 -> Bad |
| R21 | 7 | EQUIVALENT | (empty trace) |

#### Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 21, 'structural_change': 2}`
- Operations: `{'DELETE_NODE': 1, 'INSERT_NODE': 1, 'DELETE_FLOW': 1, 'FLOW_CONDITION_CHANGE': 1, 'GATEWAY_TYPE_CHANGE': 1, 'INSERT_FLOW': 3}`
- Needs review: False
