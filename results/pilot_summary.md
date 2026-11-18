# Evaluation Harness — pilot

Dataset: `bpmndiff-synthetic-v1` · 5 bases · 30 pairs

Metrics are operation-level: a prediction matches ground truth when the canonical change type and the element/endpoints identity agree.

## Overall by mode and scenario

| Mode | Scenario | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| id | keep_ids | 59 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| id | new_ids | 29 | 687 | 30 | 0.041 | 0.492 | 0.075 |
| id | all | 88 | 687 | 30 | 0.114 | 0.746 | 0.197 |
| name | keep_ids | 50 | 295 | 9 | 0.145 | 0.847 | 0.248 |
| name | new_ids | 50 | 301 | 9 | 0.142 | 0.847 | 0.244 |
| name | all | 100 | 596 | 18 | 0.144 | 0.847 | 0.246 |
| structure | keep_ids | 28 | 346 | 31 | 0.075 | 0.475 | 0.129 |
| structure | new_ids | 28 | 346 | 31 | 0.075 | 0.475 | 0.129 |
| structure | all | 56 | 692 | 62 | 0.075 | 0.475 | 0.129 |
| hybrid | keep_ids | 59 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| hybrid | new_ids | 59 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| hybrid | all | 118 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Per change type (all scenarios)

| Change type | Mode | Support | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| INSERT_NODE | id | 14 | 14 | 228 | 0 | 0.058 | 1.000 | 0.109 |
| INSERT_NODE | name | 14 | 14 | 144 | 0 | 0.089 | 1.000 | 0.163 |
| INSERT_NODE | structure | 14 | 10 | 214 | 4 | 0.045 | 0.714 | 0.084 |
| INSERT_NODE | hybrid | 14 | 14 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_NODE | id | 6 | 6 | 228 | 0 | 0.026 | 1.000 | 0.050 |
| DELETE_NODE | name | 6 | 6 | 144 | 0 | 0.040 | 1.000 | 0.077 |
| DELETE_NODE | structure | 6 | 2 | 214 | 4 | 0.009 | 0.333 | 0.018 |
| DELETE_NODE | hybrid | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_NODE | id | 12 | 6 | 0 | 6 | 1.000 | 0.500 | 0.667 |
| RENAME_NODE | name | 12 | 12 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_NODE | structure | 12 | 4 | 8 | 8 | 0.333 | 0.333 | 0.333 |
| RENAME_NODE | hybrid | 12 | 12 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| NODE_TYPE_CHANGE | id | 8 | 4 | 0 | 4 | 1.000 | 0.500 | 0.667 |
| NODE_TYPE_CHANGE | name | 8 | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| NODE_TYPE_CHANGE | structure | 8 | 4 | 0 | 4 | 1.000 | 0.500 | 0.667 |
| NODE_TYPE_CHANGE | hybrid | 8 | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MARKER_CHANGE | id | 6 | 3 | 0 | 3 | 1.000 | 0.500 | 0.667 |
| MARKER_CHANGE | name | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MARKER_CHANGE | structure | 6 | 4 | 0 | 2 | 1.000 | 0.667 | 0.800 |
| MARKER_CHANGE | hybrid | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MOVE_LANE | id | 4 | 2 | 0 | 2 | 1.000 | 0.500 | 0.667 |
| MOVE_LANE | name | 4 | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| MOVE_LANE | structure | 4 | 2 | 4 | 2 | 0.333 | 0.500 | 0.400 |
| MOVE_LANE | hybrid | 4 | 4 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_LANE | id | 2 | 1 | 0 | 1 | 1.000 | 0.500 | 0.667 |
| RENAME_LANE | name | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| RENAME_LANE | structure | 2 | 0 | 0 | 2 | 0.000 | 0.000 | 0.000 |
| RENAME_LANE | hybrid | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_LANE | id | 0 | 0 | 1 | 0 | 0.000 | 1.000 | 0.000 |
| INSERT_LANE | structure | 0 | 0 | 2 | 0 | 0.000 | 1.000 | 0.000 |
| DELETE_LANE | id | 0 | 0 | 1 | 0 | 0.000 | 1.000 | 0.000 |
| DELETE_LANE | structure | 0 | 0 | 2 | 0 | 0.000 | 1.000 | 0.000 |
| GATEWAY_TYPE_CHANGE | id | 6 | 3 | 0 | 3 | 1.000 | 0.500 | 0.667 |
| GATEWAY_TYPE_CHANGE | name | 6 | 0 | 0 | 6 | 0.000 | 0.000 | 0.000 |
| GATEWAY_TYPE_CHANGE | structure | 6 | 2 | 0 | 4 | 1.000 | 0.333 | 0.500 |
| GATEWAY_TYPE_CHANGE | hybrid | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| INSERT_FLOW | id | 36 | 36 | 229 | 0 | 0.136 | 1.000 | 0.239 |
| INSERT_FLOW | name | 36 | 36 | 305 | 0 | 0.106 | 1.000 | 0.191 |
| INSERT_FLOW | structure | 36 | 24 | 248 | 12 | 0.088 | 0.667 | 0.156 |
| INSERT_FLOW | hybrid | 36 | 36 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DELETE_FLOW | id | 14 | 7 | 0 | 7 | 1.000 | 0.500 | 0.667 |
| DELETE_FLOW | name | 14 | 8 | 3 | 6 | 0.727 | 0.571 | 0.640 |
| DELETE_FLOW | structure | 14 | 0 | 0 | 14 | 0.000 | 0.000 | 0.000 |
| DELETE_FLOW | hybrid | 14 | 14 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| FLOW_CONDITION_CHANGE | id | 8 | 4 | 0 | 4 | 1.000 | 0.500 | 0.667 |
| FLOW_CONDITION_CHANGE | name | 8 | 2 | 0 | 6 | 1.000 | 0.250 | 0.400 |
| FLOW_CONDITION_CHANGE | structure | 8 | 2 | 0 | 6 | 1.000 | 0.250 | 0.400 |
| FLOW_CONDITION_CHANGE | hybrid | 8 | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DATA_CHANGE | id | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DATA_CHANGE | name | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DATA_CHANGE | structure | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| DATA_CHANGE | hybrid | 2 | 2 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## ID-regeneration effect

The `new_ids` scenario regenerates every XML ID while keeping the model semantics and the injected mutations identical to `keep_ids`. The gap between the two scenarios isolates identifier dependence.

- **id**: keep 1.000 → new IDs 0.075 (Δ -0.925)
- **name**: keep 0.248 → new IDs 0.244 (Δ -0.004)
- **structure**: keep 0.129 → new IDs 0.129 (Δ +0.000)
- **hybrid**: keep 1.000 → new IDs 1.000 (Δ +0.000)
