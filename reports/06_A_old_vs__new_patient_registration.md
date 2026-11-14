# Pairwise comparison: Registration of old patients vs General new patient registration

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | xpdl | 12 | 12 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/51.Mini hospital (FO).Registration of old patients/Diagram 1.xpdl |
| Variant | xpdl | 12 | 12 | /home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset/52.Mini hospital (FO).General new patient registration/Diagram 1.xpdl |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 8 | 0 | 2 | 2 | 2 | 0 |

## Edit script (12 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | DELETE_NODE | Reads the Patient and Insurance database | removed task | no |
| 1. Steps (tasks and events) | DELETE_NODE | Displays the query result | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Enter the patient's address | added task | no |
| 1. Steps (tasks and events) | INSERT_NODE | displays the registration information to a table in the form | added task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Enters the medical record ID | "Enters the medical record ID" -> "Enters the patient's identity" (meaning_changed) | no |
| 1. Steps (tasks and events) | RENAME_NODE | Wants to register old patients | "Wants to register old patients" -> "Wants to register a new general patient" (meaning_changed) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Saves the registration information -> <exclusive gateway (XOR)> | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Enter the patient's address -> Selects the register button | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Enters the patient's identity -> Enter the patient's address | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Saves the registration information -> displays the registration information to a table in the form | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | displays the registration information to a table in the form -> <exclusive gateway (XOR)> | flow added (1x) | no |
| 5. Data and cross-pool communication | DATA_CHANGE | Insurance | data store removed: "Insurance" | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Wants to register old patients -> Queries District, Subdistric, Village, and Referral -> Displays a registration form -> Enters the medical record ID -> Enter the patient's address -> Selects the register button`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (46 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R04 | 2 | EQUIVALENT | (empty trace) |
| R08 | 3 | EQUIVALENT | (empty trace) |
| R13 | 3 | NOT EQUIVALENT | Saves the registration information |
| R17 | 4 | NOT EQUIVALENT | Enters the medical record ID -> Enter the patient's address -> Selects the register button |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'unchanged': 8, 'semantic_change': 2, 'structural_change': 4}`
- Operations: `{'DELETE_NODE': 2, 'INSERT_NODE': 2, 'RENAME_NODE': 2, 'DELETE_FLOW': 1, 'INSERT_FLOW': 4, 'DATA_CHANGE': 1}`
- Needs review: False