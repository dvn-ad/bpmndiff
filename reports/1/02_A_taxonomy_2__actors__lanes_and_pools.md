# Pairwise comparison: Payment Settlement (v1) vs Payment Settlement (v2)

| Model | Format | Nodes | Flows | Source |
|---|---|---|---|---|
| Reference | bpmn | 6 | 5 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario2_actors_v1.bpmn |
| Variant | bpmn | 6 | 5 | /home/mendoan/Projects/bpmndiff/dataset/taxonomy_variants/scenario2_actors_v2.bpmn |

## Alignment Summary

| Identical | Synonym | Meaning Changed | Deleted | Inserted | Needs Review |
|---|---|---|---|---|---|
| 6 | 0 | 0 | 0 | 0 | 0 |

## Edit script (3 operations)

| Category | Operation | Element | Detail | Review |
|---|---|---|---|---|
| 2. Actors (lanes and pools) | MOVE_LANE | Print receipt | Print receipt: "Cashier" -> "Operations" | no |
| 2. Actors (lanes and pools) | RENAME_LANE | Cashier | "Cashier" -> "Cashier Officer" | no |
| 2. Actors (lanes and pools) | RENAME_LANE | Temporary Staff | "Temporary Staff" -> "Auditor" | no |

## Behavioural verification

- Trace equivalence: **EQUIVALENT**
- Method: `trace_equivalence (tau-closure + subset construction)`
- Branching bisimulation: **EQUIVALENT**

## SESE fragments (15 regions)

_No affected region._

## Fusion verdict

**non_behavioral_swimlane_change**

- Element verdicts: `{'unchanged': 6}`
- Operations: `{'MOVE_LANE': 1, 'RENAME_LANE': 2}`
- Needs review: False