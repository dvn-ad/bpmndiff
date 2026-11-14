# Pairwise comparison: General patient cashier vs Down payment

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | xpdl | 22 | 23 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/58.Mini hospital (cashier).General patient cashier/Diagram 1.xpdl |
| Variant | xpdl | 15 | 17 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/59.Mini hospital (cashier).Down payment/Diagram 1.xpdl |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 7 | 0 | 6 | 9 | 2 | 0 |

## Edit script (31 operations)

| Operation | Element | Detail | Review |
|---|---|---|---|
| DELETE | Chooses the type of payment | removed task | no |
| DELETE | Saves the Transaction | removed task | no |
| DELETE | Selects an add button | removed task | no |
| DELETE | Prints the transaction to the printer | removed task | no |
| DELETE | Reads the Transaction Master database | removed task | no |
| DELETE | Saves the Transaction | removed task | no |
| DELETE | Adds it to the list | removed task | no |
| DELETE | Enters the transaction code, transaction type, quantity | removed task | no |
| DELETE | Displays the price | removed task | no |
| INSERT | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| INSERT | <exclusive gateway (XOR)> | added exclusive gateway (XOR) | no |
| RENAME | Enter the medical record ID | "Enter the medical record ID" -> "Enters Down Payment information" | no |
| RENAME | Displays it to the table | "Displays it to the table" -> "Saves the Down Payment information" | no |
| RENAME | Displays the query results | "Displays the query results" -> "Displays patient information" | no |
| RENAME | Wants to make a general patient payment | "Wants to make a general patient payment" -> "Wants to make a Down Payment transaction" | no |
| RENAME | Displays a general patient payment form | "Displays a general patient payment form" -> "Displays Down Payment transaction form" | no |
| RENAME | Reads the Patient and Registration Database | "Reads the Patient and Registration Database" -> "Searches for patients by register number" | no |
| DELETE_FLOW | <exclusive gateway (XOR)> -> <end event> | flow removed (1x) | no |
| DELETE_FLOW | Displays a general patient payment form -> Enter the medical record ID | flow removed (1x) | no |
| DELETE_FLOW | Reads the Patient and Registration Database -> Displays the query results | flow removed (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> <end event> | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> Displays patient information | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> Enters Down Payment information | flow added (1x) | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> Saves the Down Payment information | flow added (1x) | no |
| INSERT_FLOW | Displays Down Payment transaction form -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | Displays patient information -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | Saves the Down Payment information -> <exclusive gateway (XOR)> | flow added (1x) | no |
| INSERT_FLOW | Searches for patients by register number -> <exclusive gateway (XOR)> | flow added (1x) | no |

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
| R55 | 13 | NOT EQUIVALENT | Displays a general patient payment form -> Displays it to the table -> Enter the medical record ID -> Reads the Patient and Registration Database -> Displays the query results |
| R60 | 14 | skipped | (empty trace) |
| R69 | 17 | NOT EQUIVALENT | Reads the Patient and Registration Database |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'unchanged': 7, 'semantic_change': 6, 'structural_change': 11}`
- Operations: `{'DELETE': 9, 'INSERT': 2, 'RENAME': 6, 'DELETE_FLOW': 3, 'INSERT_FLOW': 11}`
- Needs review: False