# Pairwise comparison: Corporate new patient registration vs Corporate new patient registration using identity number

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 14 | 14 | dataset/FO 2.bpmn |
| Variant | bpmn | 14 | 14 | dataset/FO 3.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 11 | 2 | 1 | 0 | 0 | 0 |

## Edit script (6 operations)

| Operation | Element | Detail | Review |
|---|---|---|---|
| RENAME | Enters the patient's identity | "Enters the patient's identity" -> "Enters the patient's identity number" | no |
| RENAME | Enter the patient's address | "Enter the patient's address" -> "Retrieves patient address & profile" | no |
| RENAME | Enters company information | "Enters company information" -> "Retrieves company information" | no |
| RENAME_SWIMLANE | FO | "FO" -> "Patient" | no |
| CHANGE_SWIMLANE | Enter the patient's address | Enter the patient's address: "FO" -> "System" | no |
| CHANGE_SWIMLANE | Enters company information | Enters company information: "FO" -> "System" | no |

## Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Branching bisimulation: **EQUIVALENT**

## SESE fragments (47 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R11 | 3 | EQUIVALENT | (empty trace) |
| R12 | 3 | EQUIVALENT | (empty trace) |
| R13 | 3 | EQUIVALENT | (empty trace) |

## Fusion verdict

**semantic_change**

- Element verdicts: `{'unchanged': 11, 'non_behavioral_rename': 2, 'semantic_change': 1}`
- Operations: `{'RENAME': 3, 'RENAME_SWIMLANE': 1, 'CHANGE_SWIMLANE': 2}`
- Needs review: False