# Detected-operations taxonomy

This document maps every **edit operation the prototype can detect** back to the
scope categories and compared aspects it covers. It is the operational companion
to the requirement scope matrix (Event / Activity / Gateway / Connecting object /
Swimlane / Data).

The canonical operation names and the v1 `change` + `evidence` output contract
are specified in [`docs/changes.md`](changes.md) and
[`schema/change-v1.json`](../schema/change-v1.json).

Source of truth for emission logic: `bpmndiff/diff.py` (`_build_operations`).
Fusion verdict mapping: `bpmndiff/diff.py` (`diff_models`).

## 1. Taxonomy table: detected operation → scope

| Operation | Legacy op | Category | Category name | Scope element | Compared aspects detected | Fusion verdict (typical) |
| --- | --- | --- | --- | --- | --- | --- |
| `INSERT_NODE` | `INSERT` | 1 | Steps (tasks and events) | node | added task / event / gateway | `structural_change` (or behavioural follow-up) |
| `DELETE_NODE` | `DELETE` | 1 | Steps (tasks and events) | node | removed task / event | `structural_change` |
| `RENAME_NODE` | `RENAME` | 1 | Steps (tasks and events) | node | label change; split into `synonym` vs `meaning_changed` | `non_behavioral_rename` / `semantic_change` / `structural_change` |
| `NODE_TYPE_CHANGE` | `CHANGE_TYPE` | 1 | Steps (tasks and events) | node | task-type change (user/service/manual/script/send/receive/business_rule/abstract); kind change (task/subprocess/call_activity/start/end/event/boundary_event…); event-definition change | `behavioral_change` / `semantic_change` / `structural_change` |
| `MARKER_CHANGE` | `MARKER_CHANGE` | 1 | Steps (tasks and events) | node | loop / `multi_instance_parallel` / `multi_instance_sequential` presence or absence | `behavioral_change` |
| `BOUNDARY_CHANGE` | `BOUNDARY_CHANGE` | 1 | Steps (tasks and events) | boundary_event | attached activity (`attached_to`), interrupting vs non-interrupting (`cancel_activity`), event definition | `behavioral_change` / `structural_change` |
| `MOVE_LANE` | `CHANGE_SWIMLANE` | 2 | Actors (lanes and pools) | swimlane | lane reassignment of a matched node | `non_behavioral_swimlane_change` |
| `RENAME_LANE` | `RENAME_SWIMLANE` | 2 | Actors (lanes and pools) | swimlane | lane label change | `non_behavioral_swimlane_change` |
| `INSERT_LANE` | `INSERT_LANE` | 2 | Actors (lanes and pools) | swimlane | new lane added | swimlane-level change |
| `DELETE_LANE` | `DELETE_LANE` | 2 | Actors (lanes and pools) | swimlane | lane removed | swimlane-level change |
| `GATEWAY_TYPE_CHANGE` | `CHANGE_GATEWAY_TYPE` | 3 | Sequence, flow, and branching | gateway | gateway kind change (XOR/Inclusive/Parallel/Event-based/Complex), direction (split/join) | `behavioral_change` / `semantic_change` |
| `INSERT_FLOW` | `INSERT_FLOW` | 3 | Sequence, flow, and branching | flow | sequence flow added (source/target) | `structural_change` |
| `DELETE_FLOW` | `DELETE_FLOW` | 3 | Sequence, flow, and branching | flow | sequence flow removed | `structural_change` |
| `FLOW_CONDITION_CHANGE` | `FLOW_CONDITION_CHANGE` | 3 | Sequence, flow, and branching | flow | condition or default flow change | `behavioral_change`* |
| `REORDER` | `REORDER` | 3 | Sequence, flow, and branching | node | swapped execution order between two tasks | `behavioral_change` |
| `PARALLELIZE` | `PARALLELIZE` | 3 | Sequence, flow, and branching | node | sequential → parallel (via AND split) | `behavioral_change` |
| `SEQUENTIALIZE` | `SEQUENTIALIZE` | 3 | Sequence, flow, and branching | node | parallel → sequential | `behavioral_change` |
| `EXTRACT_SUBPROCESS` | `EXTRACT_SUBPROCESS` | 4 | Sub-process structure | subprocess | tasks extracted into sub-process / call activity | `structural_change` |
| `INLINE_SUBPROCESS` | `INLINE_SUBPROCESS` | 4 | Sub-process structure | subprocess | sub-process inlined back into tasks | `structural_change` |
| `MESSAGE_FLOW_CHANGE` | `MESSAGE_FLOW_CHANGE` | 5 | Data and cross-pool communication | message_flow | message flow added / removed / retargeted across pools | fusion verdict on endpoints |
| `DATA_CHANGE` | `DATA_CHANGE` | 5 | Data and cross-pool communication | data | data object / store / input / output added / removed | fusion verdict on data element |

\* `FLOW_CONDITION_CHANGE` is *detected* reliably; whether it implies a behavioural
difference depends on whether the condition participates in the LTS execution.

## 2. Scope → detectable operation(s)

| Scope category | Compared aspects | Detected operation(s) |
| --- | --- | --- |
| **Event** | Start / intermediate (catch & throw) / end; type; definition (none, message, timer, error, signal, conditional, escalation, compensation, link, terminate); label; lane | `NODE_TYPE_CHANGE` (kind + event definition), `RENAME_NODE` (label), `BOUNDARY_CHANGE` (attached / interrupting / definition), lane ops |
| **Event** | Boundary event | `BOUNDARY_CHANGE` |
| **Activity** | Task (user, service, manual, script, send, receive, business rule); label, type, lane | `NODE_TYPE_CHANGE` (task type / kind), `RENAME_NODE`, lane ops |
| **Activity** | Sub-process (collapsed/expanded) + call activity; label, content, called process | `EXTRACT_SUBPROCESS`, `INLINE_SUBPROCESS` |
| **Activity** | Loop and multi-instance markers (parallel, sequential) | `MARKER_CHANGE`, `PARALLELIZE`, `SEQUENTIALIZE` |
| **Gateway** | Exclusive / Inclusive / Parallel / Event-based / Complex; type, split/join direction, default flow | `GATEWAY_TYPE_CHANGE`, `FLOW_CONDITION_CHANGE` (default flow), `PARALLELIZE`/`SEQUENTIALIZE` |
| **Connecting object** | Sequence flow (source, target, condition, default) | `INSERT_FLOW`, `DELETE_FLOW`, `FLOW_CONDITION_CHANGE` |
| **Connecting object** | Message flow (source/target across pools) | `MESSAGE_FLOW_CHANGE` |
| **Swimlane** | Pool / lane / nested lane; label, elements | `RENAME_LANE`, `MOVE_LANE`, `INSERT_LANE`, `DELETE_LANE` |
| **Data** | Data object / store / input / output; label, connected elements | `DATA_CHANGE` |

## 3. Fusion verdicts produced from these operations

| Condition | Verdict | Meaning |
| --- | --- | --- |
| No operations | — | `identical` (equivalent by construction) |
| `needs_review` | `needs_review` | low-confidence alignment |
| `meaning_changed` + not equivalent | `semantic_and_behavioral_change` | semantic + behavioural change |
| `meaning_changed` only | `semantic_change` | label meaning changed, behaviour equivalent |
| Not equivalent | `behavioral_change` | structural/control-flow behaviour differs |
| Matched + equivalent + same label | `unchanged` | identical |
| Matched + equivalent + renamed | `non_behavioral_rename` | pure rename |
| Lane-only changes | — | `non_behavioral_swimlane_change` |
| Exploration truncated | — | `inconclusive_behavior` |

## 3b. Semantic detection layer (pair labelling)

The semantic stage resolves *what a label pair means*, before fusion:

| Mechanism | Code | Trigger | Label produced | Fusion effect |
| --- | --- | --- | --- | --- |
| Exact normalised label | `normalize_label` | equal after lowercasing / punctuation / whitespace normalisation | `identical` | unchanged |
| Typo / spelling variant (1-token labels) | `label_similarity` | `SequenceMatcher.ratio ≥ 0.80` or Jaro-Winkler char-similarity ≥ 0.85 | high score (capped 0.95) → `synonym` if ≥ `synonym_threshold` (0.72) | treated as synonym → `non_behavioral_rename` when behaviour confirms equivalence |
| Synonym (canonical token equivalence) | `canonical_tokens` + `_SYNONYMS` / `_PHRASES` | canonical token sets equal | `synonym` (score 0.94) | `non_behavioral_rename` |
| Meaning change | `_CONTRAST_GROUPS` | different members of the same contrast group (`general`↔`corporate`, `old`↔`new`, `inpatient`↔`outpatient`, …) | `meaning_changed` (score capped ≤ 0.68) | `semantic_change`, plus behavioural check |
| Ambiguous | `label_similarity` mid-range | score in `[review_low, review_high)` | `needs_review` | LLM adjudication (opt-in) or manual review |

Resolution order in `_initial_pairs`: normalised labels equal → `identical`;
else score ≥ 0.72 → `synonym`; else → `meaning_changed`. A pure rename
(synonym + equivalent behaviour) results in a `RENAME_NODE` with subtype
`synonym`; a semantic change results in subtype `meaning_changed`.

## 4. Current implementation status of the taxonomy

- **Fully implemented**: operation emission, category assignment, fusion mapping, reporting (`bpmndiff/diff.py`, `bpmndiff/report.py`).
- **Partially implemented**: behavioural depth behind some operations (see `docs/PROTOTYPE.md`, "Known gaps") — e.g. conditions/data/messages/sub-process interiors are compared but not yet executed inside the LTS.
- **Not implemented**: Visio `.vdx` support; canonical RPST decomposition (dominator approximation instead); full nested-lane semantics.
