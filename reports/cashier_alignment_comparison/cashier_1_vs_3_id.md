# Pairwise comparison: Down payment vs Print receipt

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 19 | 21 | dataset\Cashier 1.bpmn |
| Variant | bpmn | 19 | 21 | dataset\Cashier 3.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 19 | 19 | 0 |

## Edit script (61 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Invisible Task | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | Enters Down Payment information | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Saves the Down Payment information | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Displays patient information | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Invisible Task | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | Invisible Task | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | Wants to make a Down Payment transaction | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <start event> | removed start event | no |
| 1. Steps (tasks and events) | DELETE_NODE | <end event> | removed end event | no |
| 1. Steps (tasks and events) | DELETE_NODE | Displays Down Payment transaction form | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | Searches for patients by register number | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Invisible Task | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | <exclusive gateway (XOR)> | removed exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | DELETE_NODE | Selects a save button | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | <end event> | added end event | no |
| 1. Steps (tasks and events) | INSERT_NODE | Displays the message data not found | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | <start event> | added start event | no |
| 1. Steps (tasks and events) | INSERT_NODE | Wants to make Reprint hospitalization receipts | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Invisible Task | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Invisible Task | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Displays payment information | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Prints the receipt | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | Displays the Reprint hospitalization receipts form | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | Searches for the receipt number | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Invisible Task | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Selects a print button | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Enters the receipt number | added task | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <end event> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Displays payment information | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Displays the message data not found | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Enters the receipt number | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Invisible Task | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Invisible Task | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Invisible Task | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Prints the receipt | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Selects a print button | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <start event> -> Wants to make Reprint hospitalization receipts | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays payment information -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays the Reprint hospitalization receipts form -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays the message data not found -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Enters the receipt number -> Searches for the receipt number | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Invisible Task -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Invisible Task -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Invisible Task -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Prints the receipt -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Searches for the receipt number -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Selects a print button -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Wants to make Reprint hospitalization receipts -> Displays the Reprint hospitalization receipts form | flow added (1x) | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Receipt | data store added: "Receipt" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Patient | data store removed: "Patient" | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to make Reprint hospitalization receipts -> Displays the Reprint hospitalization receipts form -> Enters the receipt number -> Searches for the receipt number -> Displays payment information -> Invisible Task -> Selects a print button -> Invisible Task`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (23 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R00 | 2 | skipped | (empty trace) |
| R01 | 2 | skipped | (empty trace) |
| R04 | 5 | skipped | (empty trace) |
| R05 | 5 | skipped | (empty trace) |
| R07 | 10 | skipped | (empty trace) |

## Fusion verdict

**behavioral_change**

- Element verdicts: `{'structural_change': 38}`
- Operations: `{'DELETE_NODE': 19, 'INSERT_NODE': 19, 'INSERT_FLOW': 21, 'DATA_CHANGE': 2}`
- Needs review: False