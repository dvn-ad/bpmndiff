# Pairwise comparison: General patient cashier vs Down payment

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | xpdl | 22 | 23 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/58.Mini hospital (cashier).General patient cashier/Diagram 1.xpdl |
| Variant | xpdl | 15 | 17 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/59.Mini hospital (cashier).Down payment/Diagram 1.xpdl |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 7 | 0 | 6 | 9 | 2 | 0 |

## Edit script (45 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Chooses the type of payment | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Saves the Transaction | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Selects an add button | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Prints the transaction to the printer | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Reads the Transaction Master database | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Saves the Transaction | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Adds it to the list | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Enters the transaction code, transaction type, quantity | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Displays the price | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | INSERT_NODE | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enter the medical record ID | "Enter the medical record ID" -> "Enters Down Payment information" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays it to the table | "Displays it to the table" -> "Saves the Down Payment information" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays the query results | "Displays the query results" -> "Displays patient information" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Wants to make a general patient payment | "Wants to make a general patient payment" -> "Wants to make a Down Payment transaction" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Displays a general patient payment form | "Displays a general patient payment form" -> "Displays Down Payment transaction form" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Reads the Patient and Registration Database | "Reads the Patient and Registration Database" -> "Searches for patients by register number" (meaning_changed) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | <exclusive gateway (XOR)> -> <end event> | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | <exclusive gateway (XOR)> -> Selects a save button | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Displays a general patient payment form -> Enter the medical record ID | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Reads the Patient and Registration Database -> Displays the query results | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <end event> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Displays patient information | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Enters Down Payment information | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Saves the Down Payment information | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | <exclusive gateway (XOR)> -> Selects a save button | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays Down Payment transaction form -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Displays patient information -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Saves the Down Payment information -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Searches for patients by register number -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "<exclusive gateway (XOR)>" and "<exclusive gateway (XOR)>" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "<exclusive gateway (XOR)>" and "<exclusive gateway (XOR)>" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "<exclusive gateway (XOR)>" and "<exclusive gateway (XOR)>" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "<exclusive gateway (XOR)>" and "Selects a save button" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "Displays it to the table" and "<exclusive gateway (XOR)>" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "Displays it to the table" and "<exclusive gateway (XOR)>" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "Displays it to the table" and "Selects a save button" | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "Selects a save button" and "<exclusive gateway (XOR)>" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Registration | data store removed: "Registration" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Transaction | data store removed: "Transaction" | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to make a general patient payment -> Displays a general patient payment form -> Enter the medical record ID -> Reads the Patient and Registration Database -> Enter the medical record ID -> Reads the Patient and Registration Database -> Selects a save button`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (79 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R13 | 3 | NOT EQUIVALENT | Enter the medical record ID -> Wants to make a general patient payment -> Displays a general patient payment form |
| R19 | 3 | EQUIVALENT | (empty trace) |
| R60 | 14 | skipped | (empty trace) |
| R73 | 19 | NOT EQUIVALENT | Displays a general patient payment form -> Enter the medical record ID -> Reads the Patient and Registration Database -> Enter the medical record ID -> Reads the Patient and Registration Database -> Selects a save button |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'unchanged': 7, 'semantic_change': 6, 'structural_change': 11}`
- Operations: `{'DELETE_NODE': 9, 'INSERT_NODE': 2, 'RENAME_NODE': 6, 'DELETE_FLOW': 5, 'INSERT_FLOW': 13, 'REORDER': 8, 'DATA_CHANGE': 2}`
- Needs review: False