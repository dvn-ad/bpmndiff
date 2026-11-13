# Pairwise comparison: Down payment vs Print receipt

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 19 | 21 | dataset/Cashier 1.bpmn |
| Variant | bpmn | 19 | 21 | dataset/Cashier 2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 11 | 2 | 5 | 1 | 1 | 0 |

## Edit script (11 operations)

| Operation | Element | Detail | Review |
|---|---|---|---|
| DELETE | Invisible Task | removed task | no |
| INSERT | Displays the message data not found | added task | no |
| RENAME | Enters Down Payment information | "Enters Down Payment information" -> "Enters the receipt number" | no |
| RENAME | Saves the Down Payment information | "Saves the Down Payment information" -> "Prints the receipt" | no |
| RENAME | Displays patient information | "Displays patient information" -> "Displays payment information" | no |
| RENAME | Wants to make a Down Payment transaction | "Wants to make a Down Payment transaction" -> "Wants to make Reprint hospitalization receipts" | no |
| RENAME | Displays Down Payment transaction form | "Displays Down Payment transaction form" -> "Displays the Reprint hospitalization receipts form" | no |
| RENAME | Searches for patients by register number | "Searches for patients by register number" -> "Searches for the receipt number" | no |
| RENAME | Selects a save button | "Selects a save button" -> "Selects a print button" | no |
| INSERT_FLOW | <exclusive gateway (XOR)> -> Displays the message data not found | flow added (1x) | no |
| INSERT_FLOW | Displays the message data not found -> <exclusive gateway (XOR)> | flow added (1x) | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Displays the message data not found -> Invisible Task -> Selects a save button -> Invisible Task`
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

- Element verdicts: `{'behavioral_change': 2, 'semantic_change': 5, 'unchanged': 11, 'structural_change': 2}`
- Operations: `{'DELETE': 1, 'INSERT': 1, 'RENAME': 7, 'INSERT_FLOW': 2}`
- Needs review: False