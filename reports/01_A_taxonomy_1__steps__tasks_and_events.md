# Pairwise comparison: Patient Registration (v1) vs Patient Registration (v2)

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 8 | 6 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario1_steps_v1.bpmn |
| Variant | bpmn | 8 | 6 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario1_steps_v2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 5 | 1 | 1 | 1 | 1 | 0 |

## Edit script (9 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | BOUNDARY_CHANGE | Timeout limit | attached: "t_check" -> "t_check", interrupting: True -> False | no |
| 1. Steps (tasks and events) | DELETE_NODE | Take paper form | removed task | no |
| 1. Steps (tasks and events) | INSERT_NODE | Verify insurance eligibility | added task | no |
| 1. Steps (tasks and events) | MARKER_CHANGE | Notify doctors | marker: "none" -> "multi_instance_parallel" | no |
| 1. Steps (tasks and events) | NODE_TYPE_CHANGE | Check ID | user task -> service task | no |
| 1. Steps (tasks and events) | RENAME_NODE | Save patient data | "Save patient data" -> "Store patient data" (synonym) | no |
| 1. Steps (tasks and events) | RENAME_NODE | General patient intake | "General patient intake" -> "Corporate patient intake" (meaning_changed) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Patient arrives -> Verify insurance eligibility | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Verify insurance eligibility -> Check ID | flow added (1x) | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (reference_only): `Take paper form -> Check ID -> Save patient data -> General patient intake -> Notify doctors`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (16 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R-root | 8 | NOT EQUIVALENT | Take paper form -> Check ID -> Save patient data -> General patient intake -> Notify doctors |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'unchanged': 3, 'behavioral_change': 2, 'non_behavioral_rename': 1, 'semantic_change': 1, 'structural_change': 2}`
- Operations: `{'BOUNDARY_CHANGE': 1, 'DELETE_NODE': 1, 'INSERT_NODE': 1, 'MARKER_CHANGE': 1, 'NODE_TYPE_CHANGE': 1, 'RENAME_NODE': 2, 'INSERT_FLOW': 2}`
- Needs review: False