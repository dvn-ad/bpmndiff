# Pairwise comparison: Lab Diagnostics (v1) vs Lab Diagnostics (v2)

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 4 | 3 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario5_data_and_messages_v1.bpmn |
| Variant | bpmn | 4 | 3 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario5_data_and_messages_v2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 4 | 0 | 0 | 0 | 0 | 0 |

## Edit script (3 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 5. Data and cross-pool communication | DATA_CHANGE | PatientEMR | data store added: "PatientEMR" | no |
| 5. Data and cross-pool communication | DATA_CHANGE | LabReportsDB | data store removed: "LabReportsDB" | no |
| 5. Data and cross-pool communication | MESSAGE_FLOW_CHANGE | Send test sample | message flow added from "t_order" to "p_lab" | no |

## Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Branching bisimulation: **EQUIVALENT**

## SESE fragments (6 regions)

_No affected region._

## Fusion verdict

**unchanged**

- Element verdicts: `{'unchanged': 4}`
- Operations: `{'DATA_CHANGE': 2, 'MESSAGE_FLOW_CHANGE': 1}`
- Needs review: False