# Pairwise comparison: Down payment vs Print receipt

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 19 | 21 | dataset\Cashier 1.bpmn |
| Variant | bpmn | 19 | 21 | dataset\Cashier 2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 11 | 2 | 6 | 0 | 0 | 2 |

## Edit script (10 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | RENAME_NODE | Enters Down Payment information | "Enters Down Payment information" -> "Enters the receipt number" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Saves the Down Payment information | "Saves the Down Payment information" -> "Prints the receipt" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays patient information | "Displays patient information" -> "Displays payment information" (synonym) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Invisible Task | "Invisible Task" -> "Displays the message data not found" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Wants to make a Down Payment transaction | "Wants to make a Down Payment transaction" -> "Wants to make Reprint hospitalization receipts" (meaning_changed) | yes |
| 1. Steps (tasks and events) | RENAME_NODE | Displays Down Payment transaction form | "Displays Down Payment transaction form" -> "Displays the Reprint hospitalization receipts form" (meaning_changed) | yes |
| 1. Steps (tasks and events) | RENAME_NODE | Searches for patients by register number | "Searches for patients by register number" -> "Searches for the receipt number" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Selects a save button | "Selects a save button" -> "Selects a print button" (synonym) | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Patient | data store removed: "Patient" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Receipt | data store added: "Receipt" | no |

## Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Branching bisimulation: **EQUIVALENT**

## SESE fragments (23 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R02 | 3 | EQUIVALENT | (empty trace) |
| R10 | 12 | EQUIVALENT | (empty trace) |
| R15 | 15 | skipped | (empty trace) |

## Fusion verdict

**semantic_change**

- Element verdicts: `{'unchanged': 11, 'semantic_change': 4, 'non_behavioral_rename': 2, 'needs_review': 2}`
- Operations: `{'RENAME_NODE': 8, 'DATA_CHANGE': 2}`
- Needs review: True