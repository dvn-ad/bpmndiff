# Error analysis — three most frequent failure patterns

Counts aggregate the `keep_ids` and `new_ids` scenarios. Each pattern lists one concrete generated pair that can be inspected directly in `dataset/synthetic/`.

## 1. FP · `INSERT_FLOW` · mode `name`

- Frequency: **305** occurrences (`keep_ids`, `new_ids`)
- Example pair: `dataset/synthetic/56/k1_keep.bpmn`
- Example identity: `('INSERT_FLOW', 'Id_ffd9beac-13dd-4c0f-9c58-f3f304cf90f3', 'Id_b210868a-cf5c-4157-b86e-b21d426d3851')`
- Likely cause: label-only alignment leaves unnamed gateways and events unmatched, producing structural false positives around every branch.

## 2. FP · `INSERT_FLOW` · mode `structure`

- Frequency: **248** occurrences (`keep_ids`, `new_ids`)
- Example pair: `dataset/synthetic/56/k2_keep.bpmn`
- Example identity: `('INSERT_FLOW', 'Id_1164e919-3f27-4d09-9a69-2a33a2e98847', 'Id_ac3f7a9c-28e9-4a90-8928-edfd64206da8')`
- Likely cause: the structural fingerprint is not unique on both sides (parallel branches or repeated gateway shapes), and the strategy skips every colour group that is not a singleton.

## 3. FP · `INSERT_FLOW` · mode `id`

- Frequency: **229** occurrences (`new_ids`)
- Example pair: `dataset/synthetic/56/k1_newids.bpmn`
- Example identity: `('INSERT_FLOW', 'Id_1164e919-3f27-4d09-9a69-2a33a2e98847', 'Id_ac3f7a9c-28e9-4a90-8928-edfd64206da8')`
- Likely cause: ID-only alignment cannot match nodes after a full re-export, so every node becomes an insert/delete and the real edit is buried.
