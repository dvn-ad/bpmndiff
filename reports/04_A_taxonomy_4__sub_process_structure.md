# Pairwise comparison: Clinical and Billing Check (v1) vs Clinical and Billing Check (v2)

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 7 | 4 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario4_subprocesses_v1.bpmn |
| Variant | bpmn | 7 | 4 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario4_subprocesses_v2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 6 | 0 | 1 | 0 | 0 | 0 |

## Edit script (11 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 1. Steps (tasks and events) | RENAME_NODE | Billing verification | "Billing verification" -> "Clinical verification" (meaning_changed) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Admission request -> Verify lab results | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Billing verification -> Admission approved | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Consult specialist -> Billing verification | flow removed (1x) | no |
| 3. Sequence, flow, and branching | DELETE_FLOW | Verify lab results -> Consult specialist | flow removed (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Admission request -> Clinical verification | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Authorize discount -> Admission approved | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Check insurance coverage -> Authorize discount | flow added (1x) | no |
| 3. Sequence, flow, and branching | INSERT_FLOW | Clinical verification -> Check insurance coverage | flow added (1x) | no |
| 4. Sub-process structure | EXTRACT_SUBPROCESS | ? | elements ['Consult specialist', 'Verify lab results'] extracted into sub-process "Clinical verification" | no |
| 4. Sub-process structure | INLINE_SUBPROCESS | ? | sub-process "Billing verification" inlined into root tasks ['Authorize discount', 'Check insurance coverage'] | no |

## Behavioural verification

- Trace equivalence: **NOT EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Counterexample (variant_only): `Billing verification -> Check insurance coverage -> Authorize discount`
  - only this model can execute the differing task and still complete
- Branching bisimulation: **NOT EQUIVALENT**

## SESE fragments (7 regions)

| Region | Nodes | Behaviour | Counterexample |
|---|---|---|---|
| R-root | 7 | NOT EQUIVALENT | Billing verification -> Check insurance coverage -> Authorize discount |

## Fusion verdict

**semantic_and_behavioral_change**

- Element verdicts: `{'unchanged': 6, 'semantic_change': 1}`
- Operations: `{'RENAME_NODE': 1, 'DELETE_FLOW': 4, 'INSERT_FLOW': 4, 'EXTRACT_SUBPROCESS': 1, 'INLINE_SUBPROCESS': 1}`
- Needs review: False