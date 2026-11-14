# Pairwise comparison: Patient Discharge (v1) vs Patient Discharge (v2)

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 8 | 8 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario3_flows_v1.bpmn |
| Variant | bpmn | 10 | 11 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario3_flows_v2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 8 | 0 | 0 | 0 | 2 | 0 |

## Edit script (21 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | INSERT_NODE | Join parallel | added parallel gateway (AND) | no |
| 1. Steps (tasks and events) | INSERT_NODE | Split parallel | added parallel gateway (AND) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Book follow-up -> Merge | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Check bill status -> Issue pharmacy voucher | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Collect copay -> Check bill status | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Discharge initiated -> Verify ID | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Issue pharmacy voucher -> Book follow-up | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Verify ID -> Collect copay | flow removed (1x) | no |
| 3. Sequence, flow, and branching | FLOW_CONDITION_CHANGE | Check bill status -> Merge | default flow: True -> False | no |
| 3. Sequence, flow, and branching | GATEWAY_TYPE_CHANGE | Check bill status | XOR -> AND | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Book follow-up -> Join parallel | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Check bill status -> Split parallel | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Collect copay -> Verify ID | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Discharge initiated -> Collect copay | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Issue pharmacy voucher -> Join parallel | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Join parallel -> Merge | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Split parallel -> Book follow-up | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Split parallel -> Issue pharmacy voucher | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Verify ID -> Check bill status | flow added (1x) | no |
| 3. Sequence, flow, and branching | PARALLELIZE | ? | "Book follow-up" and "Issue pharmacy voucher" made parallel via AND gateway | no |
| 3. Sequence, flow, and branching | REORDER | ? | execution order swapped between "Verify ID" and "Collect copay" | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Collect copay -> Verify ID -> Book follow-up -> Issue pharmacy voucher`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (12 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R03 | 3 | NOT EQUIVALENT | Collect copay -> Verify ID |
| R08 | 6 | NOT EQUIVALENT | Collect copay -> Verify ID -> Book follow-up -> Issue pharmacy voucher |

## Fusion verdict

**behavioral_change**

- Element verdicts: `{'unchanged': 7, 'behavioral_change': 1, 'structural_change': 2}`
- Operations: `{'INSERT_NODE': 2, 'DELETE_FLOW': 6, 'FLOW_CONDITION_CHANGE': 1, 'GATEWAY_TYPE_CHANGE': 1, 'INSERT_FLOW': 9, 'PARALLELIZE': 1, 'REORDER': 1}`
- Needs review: False