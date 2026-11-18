# Pairwise comparison: Down payment vs Print receipt

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 19 | 21 | dataset\Cashier 1.bpmn |
| Variant | bpmn | 19 | 21 | dataset\Cashier 3.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 11 | 2 | 5 | 1 | 1 | 2 |

## Edit script (13 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Saves the Down Payment information | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Prints the receipt | added task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters Down Payment information | "Enters Down Payment information" -> "Enters the receipt number" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays patient information | "Displays patient information" -> "Displays payment information" (synonym) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Invisible Task | "Invisible Task" -> "Displays the message data not found" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Wants to make a Down Payment transaction | "Wants to make a Down Payment transaction" -> "Wants to make Reprint hospitalization receipts" (meaning_changed) | yes |
| 1. Steps (tasks and events) | RENAME_NODE | Displays Down Payment transaction form | "Displays Down Payment transaction form" -> "Displays the Reprint hospitalization receipts form" (meaning_changed) | yes |
| 1. Steps (tasks and events) | RENAME_NODE | Searches for patients by register number | "Searches for patients by register number" -> "Searches for the receipt number" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Selects a save button | "Selects a save button" -> "Selects a print button" (synonym) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Prints the receipt | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Prints the receipt -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Receipt | data store added: "Receipt" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Patient | data store removed: "Patient" | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Displays patient information -> Invisible Task -> Selects a save button -> Prints the receipt`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (23 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R02 | 3 | EQUIVALENT | (empty trace) |
| R10 | 12 | EQUIVALENT | (empty trace) |
| R15 | 15 | skipped | (empty trace) |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'behavioral_change': 2, 'semantic_change': 3, 'needs_review': 2, 'unchanged': 11, 'structural_change': 2}`
- Operations: `{'DELETE_NODE': 1, 'INSERT_NODE': 1, 'RENAME_NODE': 7, 'INSERT_FLOW': 2, 'DATA_CHANGE': 2}`
- Needs review: True