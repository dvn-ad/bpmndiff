"""Edit-script generation, behavioural verification and fusion verdicts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .alignment import Alignment, AlignmentConfig, align, normalize_label, relabel_map
from .bisimulation import weak_bisimilar
from .decomposition import Decomposition, Region, decompose
from .lts import build_lts, compare_trace_equivalence, enumerate_traces
from .model import KIND_LABELS, ProcessModel


@dataclass
class DiffOptions:
    max_states: int = 20000
    max_dfa_states: int = 5000
    bisimulation: bool = True
    use_llm: bool = False
    llm: object = None
    alignment_config: AlignmentConfig = field(default_factory=AlignmentConfig)


@dataclass
class Comparison:
    reference: ProcessModel
    variant: ProcessModel
    alignment: Alignment
    operations: list[dict]
    behavior: dict
    decomposition: Decomposition
    affected_regions: list[dict]
    fusion: dict
    options: DiffOptions

    def to_dict(self) -> dict:
        alignment = self.alignment.to_dict()
        for item, pair in zip(alignment["pairs"], self.alignment.pairs):
            if pair.a is not None and pair.a in self.reference.nodes:
                item["a_id"] = pair.a
                item["a"] = self.reference.nodes[pair.a].display_name
            if pair.b is not None and pair.b in self.variant.nodes:
                item["b_id"] = pair.b
                item["b"] = self.variant.nodes[pair.b].display_name
        return {
            "mode": "A",
            "reference": {
                "id": self.reference.id,
                "name": self.reference.name,
                "source": self.reference.source,
                "format": self.reference.fmt,
                "pool": self.reference.pool,
                "stats": self.reference.stats(),
            },
            "variant": {
                "id": self.variant.id,
                "name": self.variant.name,
                "source": self.variant.source,
                "format": self.variant.fmt,
                "pool": self.variant.pool,
                "stats": self.variant.stats(),
            },
            "alignment": alignment,
            "operations": self.operations,
            "behavior": self.behavior,
            "fragments": {
                "count": len(self.decomposition.regions),
                "affected": self.affected_regions,
            },
            "fusion": self.fusion,
        }


def _node_ref(model: ProcessModel, node_id: str) -> dict:
    node = model.nodes[node_id]
    return {
        "id": node.id,
        "name": node.display_name,
        "kind": node.kind,
        "kind_label": KIND_LABELS.get(node.kind, node.kind),
        "task_type": node.task_type,
        "event_definition": node.event_definition,
        "marker": node.marker,
        "attached_to": node.attached_to,
        "cancel_activity": node.cancel_activity,
        "lane": node.lane,
        "pool": node.pool,
    }


def _reachable_nodes(model: ProcessModel, start_id: str) -> set[str]:
    visited: set[str] = set()
    queue = [start_id]
    while queue:
        curr = queue.pop()
        for succ in model.successors(curr):
            if succ not in visited:
                visited.add(succ)
                queue.append(succ)
    return visited


def _parallel_pairs(model: ProcessModel) -> set[tuple[str, str]]:
    """Return pairs of task ids that run in parallel under an AND split gateway."""
    pairs: set[tuple[str, str]] = set()
    for gw in model.nodes.values():
        if gw.kind != "and":
            continue
        succs = model.successors(gw.id)
        if len(succs) < 2:
            continue
        branch_nodes: list[set[str]] = []
        for succ in succs:
            branch_nodes.append({succ} | _reachable_nodes(model, succ))

        for i in range(len(branch_nodes)):
            for j in range(i + 1, len(branch_nodes)):
                for n1 in branch_nodes[i]:
                    for n2 in branch_nodes[j]:
                        if n1 == n2:
                            continue
                        if n1 not in model.nodes or n2 not in model.nodes:
                            continue
                        if model.nodes[n1].kind not in {"task", "subprocess", "call_activity"}:
                            continue
                        if model.nodes[n2].kind not in {"task", "subprocess", "call_activity"}:
                            continue
                        pair = (min(n1, n2), max(n1, n2))
                        pairs.add(pair)
    return pairs


def _lane_operations(
    reference: ProcessModel, variant: ProcessModel, alignment: Alignment
) -> list[dict]:
    reference_lanes = set(reference.lanes) | {node.lane for node in reference.nodes.values() if node.lane}
    variant_lanes = set(variant.lanes) | {node.lane for node in variant.nodes.values() if node.lane}
    assignments: Counter[tuple[str, str]] = Counter()
    for pair in alignment.matched_pairs:
        before = reference.nodes[pair.a].lane
        after = variant.nodes[pair.b].lane
        if before and after:
            assignments[(before, after)] += 1

    rename_candidates: dict[str, list[tuple[str, int]]] = {}
    for (before, after), count in assignments.items():
        if before not in variant_lanes and after not in reference_lanes:
            rename_candidates.setdefault(before, []).append((after, count))

    lane_renames: dict[str, str] = {}
    for before, candidates in rename_candidates.items():
        best_count = max(count for _, count in candidates)
        best = [after for after, count in candidates if count == best_count]
        if len(best) != 1:
            continue
        after = best[0]
        incoming = [
            (source, count)
            for (source, target), count in assignments.items()
            if target == after
            and source not in variant_lanes
            and target not in reference_lanes
        ]
        reverse_count = max(count for _, count in incoming)
        reverse = [source for source, count in incoming if count == reverse_count]
        if reverse_count == best_count and reverse == [before]:
            lane_renames[before] = after

    operations: list[dict] = []
    for before, after in sorted(lane_renames.items()):
        operations.append(
            {
                "op": "RENAME_LANE",
                "legacy_op": "RENAME_SWIMLANE",
                "category": 2,
                "category_name": "Actors (lanes and pools)",
                "element": "swimlane",
                "before": {"name": before},
                "after": {"name": after},
                "detail": f'"{before}" -> "{after}"',
                "confidence": "high",
                "needs_review": False,
            }
        )

    for pair in alignment.matched_pairs:
        before = reference.nodes[pair.a]
        after = variant.nodes[pair.b]
        expected_lane = lane_renames.get(before.lane, before.lane)
        if expected_lane == after.lane:
            continue
        if before.lane == after.lane:
            continue
        operations.append(
            {
                "op": "MOVE_LANE",
                "legacy_op": "CHANGE_SWIMLANE",
                "category": 2,
                "category_name": "Actors (lanes and pools)",
                "element": "swimlane",
                "before": _node_ref(reference, before.id),
                "after": _node_ref(variant, after.id),
                "detail": (
                    f'{before.display_name}: "{before.lane or "(unassigned)"}" -> '
                    f'"{after.lane or "(unassigned)"}"'
                ),
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Added / deleted lanes
    for lane in sorted(variant_lanes - reference_lanes - set(lane_renames.values())):
        operations.append(
            {
                "op": "INSERT_LANE",
                "legacy_op": "INSERT_LANE",
                "category": 2,
                "category_name": "Actors (lanes and pools)",
                "element": "swimlane",
                "before": None,
                "after": {"name": lane},
                "detail": f'lane added: "{lane}"',
                "confidence": "high",
                "needs_review": False,
            }
        )
    for lane in sorted(reference_lanes - variant_lanes - set(lane_renames.keys())):
        operations.append(
            {
                "op": "DELETE_LANE",
                "legacy_op": "DELETE_LANE",
                "category": 2,
                "category_name": "Actors (lanes and pools)",
                "element": "swimlane",
                "before": {"name": lane},
                "after": None,
                "detail": f'lane removed: "{lane}"',
                "confidence": "high",
                "needs_review": False,
            }
        )

    return operations


def _build_operations(
    reference: ProcessModel, variant: ProcessModel, alignment: Alignment
) -> list[dict]:
    operations: list[dict] = _lane_operations(reference, variant, alignment)

    # Category 1: Steps & Category 3: Gateway type
    for pair in alignment.matched_pairs:
        a = reference.nodes[pair.a]
        b = variant.nodes[pair.b]

        # Gateway type change
        if a.is_gateway and b.is_gateway and a.kind != b.kind:
            operations.append(
                {
                    "op": "GATEWAY_TYPE_CHANGE",
                    "legacy_op": "CHANGE_GATEWAY_TYPE",
                    "category": 3,
                    "category_name": "Sequence, flow, and branching",
                    "element": "gateway",
                    "before": _node_ref(reference, a.id),
                    "after": _node_ref(variant, b.id),
                    "detail": f"{a.kind.upper()} -> {b.kind.upper()}",
                    "label": pair.label,
                    "confidence": pair.confidence,
                    "needs_review": pair.needs_review,
                }
            )
        # Node type change
        elif a.family != b.family:
            operations.append(
                {
                    "op": "NODE_TYPE_CHANGE",
                    "legacy_op": "CHANGE_TYPE",
                    "category": 1,
                    "category_name": "Steps (tasks and events)",
                    "element": "node",
                    "before": _node_ref(reference, a.id),
                    "after": _node_ref(variant, b.id),
                    "detail": f"{KIND_LABELS.get(a.kind, a.kind)} -> {KIND_LABELS.get(b.kind, b.kind)}",
                    "label": pair.label,
                    "confidence": pair.confidence,
                    "needs_review": pair.needs_review,
                }
            )
        elif a.family == "task" and b.family == "task":
            if a.task_type != b.task_type and (a.task_type != "abstract" or b.task_type != "abstract"):
                operations.append(
                    {
                        "op": "NODE_TYPE_CHANGE",
                        "legacy_op": "CHANGE_TYPE",
                        "category": 1,
                        "category_name": "Steps (tasks and events)",
                        "element": "node",
                        "before": _node_ref(reference, a.id),
                        "after": _node_ref(variant, b.id),
                        "detail": f"{a.task_type} task -> {b.task_type} task",
                        "label": pair.label,
                        "confidence": pair.confidence,
                        "needs_review": pair.needs_review,
                    }
                )
            elif a.kind != b.kind:
                operations.append(
                    {
                        "op": "NODE_TYPE_CHANGE",
                        "legacy_op": "CHANGE_TYPE",
                        "category": 1,
                        "category_name": "Steps (tasks and events)",
                        "element": "node",
                        "before": _node_ref(reference, a.id),
                        "after": _node_ref(variant, b.id),
                        "detail": f"{a.kind} -> {b.kind}",
                        "label": pair.label,
                        "confidence": pair.confidence,
                        "needs_review": pair.needs_review,
                    }
                )
        elif a.family == "event" and b.family == "event":
            if a.event_definition != b.event_definition or a.kind != b.kind:
                operations.append(
                    {
                        "op": "NODE_TYPE_CHANGE",
                        "legacy_op": "CHANGE_TYPE",
                        "category": 1,
                        "category_name": "Steps (tasks and events)",
                        "element": "node",
                        "before": _node_ref(reference, a.id),
                        "after": _node_ref(variant, b.id),
                        "detail": f"{a.event_definition} {a.kind} -> {b.event_definition} {b.kind}",
                        "label": pair.label,
                        "confidence": pair.confidence,
                        "needs_review": pair.needs_review,
                    }
                )

        # Marker change
        if a.marker != b.marker:
            operations.append(
                {
                    "op": "MARKER_CHANGE",
                    "legacy_op": "MARKER_CHANGE",
                    "category": 1,
                    "category_name": "Steps (tasks and events)",
                    "element": "node",
                    "before": _node_ref(reference, a.id),
                    "after": _node_ref(variant, b.id),
                    "detail": f'marker: "{a.marker}" -> "{b.marker}"',
                    "label": pair.label,
                    "confidence": pair.confidence,
                    "needs_review": pair.needs_review,
                }
            )

        # Boundary event change
        if (a.is_boundary or b.is_boundary) and (
            a.attached_to != b.attached_to or a.cancel_activity != b.cancel_activity
        ):
            operations.append(
                {
                    "op": "BOUNDARY_CHANGE",
                    "legacy_op": "BOUNDARY_CHANGE",
                    "category": 1,
                    "category_name": "Steps (tasks and events)",
                    "element": "boundary_event",
                    "before": _node_ref(reference, a.id),
                    "after": _node_ref(variant, b.id),
                    "detail": (
                        f'attached: "{a.attached_to}" -> "{b.attached_to}", '
                        f'interrupting: {a.cancel_activity} -> {b.cancel_activity}'
                    ),
                    "label": pair.label,
                    "confidence": pair.confidence,
                    "needs_review": pair.needs_review,
                }
            )

        # Rename step (with synonym vs meaning_changed distinction)
        if normalize_label(a.name) != normalize_label(b.name) and (
            a.name.strip() or b.name.strip()
        ):
            is_synonym = pair.label in {"synonym", "identical"}
            subtype = "synonym" if is_synonym else "meaning_changed"
            operations.append(
                {
                    "op": "RENAME_NODE",
                    "legacy_op": "RENAME",
                    "category": 1,
                    "category_name": "Steps (tasks and events)",
                    "element": "node",
                    "before": _node_ref(reference, a.id),
                    "after": _node_ref(variant, b.id),
                    "detail": f'"{a.display_name}" -> "{b.display_name}" ({subtype})',
                    "label": pair.label,
                    "is_synonym": is_synonym,
                    "subtype": subtype,
                    "score": round(pair.score, 3),
                    "confidence": pair.confidence,
                    "needs_review": pair.needs_review,
                }
            )

    for pair in alignment.unmatched_a:
        operations.append(
            {
                "op": "DELETE_NODE",
                "legacy_op": "DELETE",
                "category": 1,
                "category_name": "Steps (tasks and events)",
                "element": "node",
                "before": _node_ref(reference, pair.a),
                "after": None,
                "detail": f'removed {KIND_LABELS.get(reference.nodes[pair.a].kind, "node")}',
                "label": "unmatched",
                "confidence": "high",
                "needs_review": False,
            }
        )
    for pair in alignment.unmatched_b:
        operations.append(
            {
                "op": "INSERT_NODE",
                "legacy_op": "INSERT",
                "category": 1,
                "category_name": "Steps (tasks and events)",
                "element": "node",
                "before": None,
                "after": _node_ref(variant, pair.b),
                "detail": f'added {KIND_LABELS.get(variant.nodes[pair.b].kind, "node")}',
                "label": "unmatched",
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Sequence-flow changes between already-matched nodes.
    mapped_ref_flows: Counter[tuple[str, str]] = Counter()
    for edge in reference.edges:
        if edge.source in alignment.a_to_b and edge.target in alignment.a_to_b:
            mapped_ref_flows[(alignment.a_to_b[edge.source], alignment.a_to_b[edge.target])] += 1
    variant_flows: Counter[tuple[str, str]] = Counter(
        (edge.source, edge.target) for edge in variant.edges
    )

    for (source, target), count in (mapped_ref_flows - variant_flows).items():
        operations.append(
            {
                "op": "DELETE_FLOW",
                "legacy_op": "DELETE_FLOW",
                "category": 3,
                "category_name": "Sequence, flow, and branching",
                "element": "flow",
                "before": {
                    "source": reference.nodes[alignment.b_to_a[source]].display_name,
                    "target": reference.nodes[alignment.b_to_a[target]].display_name,
                    "source_id": alignment.b_to_a[source],
                    "target_id": alignment.b_to_a[target],
                },
                "after": None,
                "detail": f"flow removed ({count}x)",
                "label": "unmatched",
                "confidence": "high",
                "needs_review": False,
            }
        )
    for (source, target), count in (variant_flows - mapped_ref_flows).items():
        operations.append(
            {
                "op": "INSERT_FLOW",
                "legacy_op": "INSERT_FLOW",
                "category": 3,
                "category_name": "Sequence, flow, and branching",
                "element": "flow",
                "before": None,
                "after": {
                    "source": variant.nodes[source].display_name,
                    "target": variant.nodes[target].display_name,
                    "source_id": source,
                    "target_id": target,
                },
                "detail": f"flow added ({count}x)",
                "label": "unmatched",
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Flow condition & default flow changes between matched flows
    ref_flow_map: dict[tuple[str, str], Edge] = {
        (alignment.a_to_b[e.source], alignment.a_to_b[e.target]): e
        for e in reference.edges
        if e.source in alignment.a_to_b and e.target in alignment.a_to_b
    }
    var_flow_map: dict[tuple[str, str], Edge] = {
        (e.source, e.target): e for e in variant.edges
    }
    for endpoints, ref_e in ref_flow_map.items():
        if endpoints in var_flow_map:
            var_e = var_flow_map[endpoints]
            if (ref_e.condition != var_e.condition) or (ref_e.is_default != var_e.is_default):
                operations.append(
                    {
                        "op": "FLOW_CONDITION_CHANGE",
                        "legacy_op": "FLOW_CONDITION_CHANGE",
                        "category": 3,
                        "category_name": "Sequence, flow, and branching",
                        "element": "flow",
                        "before": {
                            "condition": ref_e.condition,
                            "is_default": ref_e.is_default,
                            "source": reference.nodes[ref_e.source].display_name,
                            "target": reference.nodes[ref_e.target].display_name,
                        },
                        "after": {
                            "condition": var_e.condition,
                            "is_default": var_e.is_default,
                            "source": variant.nodes[var_e.source].display_name,
                            "target": variant.nodes[var_e.target].display_name,
                        },
                        "detail": (
                            f'condition: "{ref_e.condition}" -> "{var_e.condition}"'
                            if ref_e.condition != var_e.condition
                            else f"default flow: {ref_e.is_default} -> {var_e.is_default}"
                        ),
                        "confidence": "high",
                        "needs_review": False,
                    }
                )

    # Category 3: REORDER
    # Check if relative execution order inverted between matched elements
    matched_nodes = [p for p in alignment.matched_pairs if p.a in reference.nodes and p.b in variant.nodes]
    ref_reach: dict[str, set[str]] = {p.a: _reachable_nodes(reference, p.a) for p in matched_nodes}
    var_reach: dict[str, set[str]] = {p.b: _reachable_nodes(variant, p.b) for p in matched_nodes}
    reordered_pairs: set[tuple[str, str]] = set()

    for i in range(len(matched_nodes)):
        for j in range(i + 1, len(matched_nodes)):
            p1, p2 = matched_nodes[i], matched_nodes[j]
            a1, a2 = p1.a, p2.a
            b1, b2 = p1.b, p2.b

            is_reordered = False
            first_ref, sec_ref = a1, a2
            first_var, sec_var = b2, b1
            if (a2 in ref_reach[a1] and a1 not in ref_reach[a2]) and (b1 in var_reach[b2] and b2 not in var_reach[b1]):
                is_reordered = True
            elif (a1 in ref_reach[a2] and a2 not in ref_reach[a1]) and (b2 in var_reach[b1] and b1 not in var_reach[b2]):
                is_reordered = True
                first_ref, sec_ref = a2, a1
                first_var, sec_var = b1, b2

            if is_reordered:
                pair_key = (min(a1, a2), max(a1, a2))
                if pair_key not in reordered_pairs:
                    reordered_pairs.add(pair_key)
                    operations.append(
                        {
                            "op": "REORDER",
                            "legacy_op": "REORDER",
                            "category": 3,
                            "category_name": "Sequence, flow, and branching",
                            "element": "node",
                            "before": {
                                "first": reference.nodes[first_ref].display_name,
                                "second": reference.nodes[sec_ref].display_name,
                            },
                            "after": {
                                "first": variant.nodes[first_var].display_name,
                                "second": variant.nodes[sec_var].display_name,
                            },
                            "detail": (
                                f'execution order swapped between '
                                f'"{reference.nodes[first_ref].display_name}" and "{reference.nodes[sec_ref].display_name}"'
                            ),
                            "confidence": "high",
                            "needs_review": False,
                        }
                    )

    # Category 3: PARALLELIZE & SEQUENTIALIZE
    ref_par = _parallel_pairs(reference)
    var_par = _parallel_pairs(variant)

    for (b1, b2) in var_par:
        a1, a2 = alignment.b_to_a.get(b1), alignment.b_to_a.get(b2)
        if a1 and a2 and a1 in reference.nodes and a2 in reference.nodes:
            pair_ref = (min(a1, a2), max(a1, a2))
            if pair_ref not in ref_par:
                # In reference, were they sequential?
                if a2 in ref_reach.get(a1, set()) or a1 in ref_reach.get(a2, set()):
                    operations.append(
                        {
                            "op": "PARALLELIZE",
                            "legacy_op": "PARALLELIZE",
                            "category": 3,
                            "category_name": "Sequence, flow, and branching",
                            "element": "node",
                            "before": {
                                "nodes": [
                                    reference.nodes[a1].display_name,
                                    reference.nodes[a2].display_name,
                                ]
                            },
                            "after": {
                                "nodes": [
                                    variant.nodes[b1].display_name,
                                    variant.nodes[b2].display_name,
                                ]
                            },
                            "detail": (
                                f'"{reference.nodes[a1].display_name}" and '
                                f'"{reference.nodes[a2].display_name}" made parallel via AND gateway'
                            ),
                            "confidence": "high",
                            "needs_review": False,
                        }
                    )

    for (a1, a2) in ref_par:
        b1, b2 = alignment.a_to_b.get(a1), alignment.a_to_b.get(a2)
        if b1 and b2 and b1 in variant.nodes and b2 in variant.nodes:
            pair_var = (min(b1, b2), max(b1, b2))
            if pair_var not in var_par:
                if b2 in var_reach.get(b1, set()) or b1 in var_reach.get(b2, set()):
                    operations.append(
                        {
                            "op": "SEQUENTIALIZE",
                            "legacy_op": "SEQUENTIALIZE",
                            "category": 3,
                            "category_name": "Sequence, flow, and branching",
                            "element": "node",
                            "before": {
                                "nodes": [
                                    reference.nodes[a1].display_name,
                                    reference.nodes[a2].display_name,
                                ]
                            },
                            "after": {
                                "nodes": [
                                    variant.nodes[b1].display_name,
                                    variant.nodes[b2].display_name,
                                ]
                            },
                            "detail": (
                                f'"{reference.nodes[a1].display_name}" and '
                                f'"{reference.nodes[a2].display_name}" made sequential from parallel'
                            ),
                            "confidence": "high",
                            "needs_review": False,
                        }
                    )

    # Category 4: Sub-process structure (EXTRACT_SUBPROCESS, INLINE_SUBPROCESS)
    ref_sub_owners: dict[str, str] = {}
    for n in reference.nodes.values():
        for child_id in n.submodel_node_ids:
            ref_sub_owners[child_id] = n.id

    var_sub_owners: dict[str, str] = {}
    for n in variant.nodes.values():
        for child_id in n.submodel_node_ids:
            var_sub_owners[child_id] = n.id

    # Group extracted tasks by variant subprocess
    extracted_by_sub: dict[str, list[str]] = {}
    for pair in alignment.matched_pairs:
        a_id, b_id = pair.a, pair.b
        if a_id not in ref_sub_owners and b_id in var_sub_owners:
            sub_id = var_sub_owners[b_id]
            extracted_by_sub.setdefault(sub_id, []).append(reference.nodes[a_id].display_name)

    for sub_id, task_names in extracted_by_sub.items():
        sub_name = variant.nodes[sub_id].display_name if sub_id in variant.nodes else sub_id
        operations.append(
            {
                "op": "EXTRACT_SUBPROCESS",
                "legacy_op": "EXTRACT_SUBPROCESS",
                "category": 4,
                "category_name": "Sub-process structure",
                "element": "subprocess",
                "before": {"tasks": task_names},
                "after": {"subprocess": sub_name},
                "detail": f'elements {task_names} extracted into sub-process "{sub_name}"',
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Group inlined tasks by reference subprocess
    inlined_by_sub: dict[str, list[str]] = {}
    for pair in alignment.matched_pairs:
        a_id, b_id = pair.a, pair.b
        if a_id in ref_sub_owners and b_id not in var_sub_owners:
            sub_id = ref_sub_owners[a_id]
            inlined_by_sub.setdefault(sub_id, []).append(variant.nodes[b_id].display_name)

    for sub_id, task_names in inlined_by_sub.items():
        sub_name = reference.nodes[sub_id].display_name if sub_id in reference.nodes else sub_id
        operations.append(
            {
                "op": "INLINE_SUBPROCESS",
                "legacy_op": "INLINE_SUBPROCESS",
                "category": 4,
                "category_name": "Sub-process structure",
                "element": "subprocess",
                "before": {"subprocess": sub_name},
                "after": {"tasks": task_names},
                "detail": f'sub-process "{sub_name}" inlined into root tasks {task_names}',
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Category 5: Data and cross-pool communication
    ref_mf_set = {(mf.source, mf.target): mf.name for mf in reference.message_flows}
    var_mf_set = {(mf.source, mf.target): mf.name for mf in variant.message_flows}

    # Normalize variant endpoints to reference node ids for alignment comparison
    mapped_var_mf: dict[tuple[str, str], str] = {}
    for (src, tgt), name in var_mf_set.items():
        m_src = alignment.b_to_a.get(src, src)
        m_tgt = alignment.b_to_a.get(tgt, tgt)
        mapped_var_mf[(m_src, m_tgt)] = name

    for (src, tgt), name in mapped_var_mf.items():
        if (src, tgt) not in ref_mf_set:
            operations.append(
                {
                    "op": "MESSAGE_FLOW_CHANGE",
                    "legacy_op": "MESSAGE_FLOW_CHANGE",
                    "category": 5,
                    "category_name": "Data and cross-pool communication",
                    "element": "message_flow",
                    "before": None,
                    "after": {"source": src, "target": tgt, "name": name},
                    "detail": f'message flow added from "{src}" to "{tgt}"',
                    "confidence": "high",
                    "needs_review": False,
                }
            )
    for (src, tgt), name in ref_mf_set.items():
        if (src, tgt) not in mapped_var_mf:
            operations.append(
                {
                    "op": "MESSAGE_FLOW_CHANGE",
                    "legacy_op": "MESSAGE_FLOW_CHANGE",
                    "category": 5,
                    "category_name": "Data and cross-pool communication",
                    "element": "message_flow",
                    "before": {"source": src, "target": tgt, "name": name},
                    "after": None,
                    "detail": f'message flow removed from "{src}" to "{tgt}"',
                    "confidence": "high",
                    "needs_review": False,
                }
            )

    # Data elements & associations
    ref_data_names = {de.name: de for de in reference.data_elements.values() if de.name}
    var_data_names = {de.name: de for de in variant.data_elements.values() if de.name}

    for name in sorted(set(var_data_names.keys()) - set(ref_data_names.keys())):
        de = var_data_names[name]
        operations.append(
            {
                "op": "DATA_CHANGE",
                "legacy_op": "DATA_CHANGE",
                "category": 5,
                "category_name": "Data and cross-pool communication",
                "element": "data",
                "before": None,
                "after": de.to_dict(),
                "detail": f'{de.kind.replace("_", " ")} added: "{de.name}"',
                "confidence": "high",
                "needs_review": False,
            }
        )
    for name in sorted(set(ref_data_names.keys()) - set(var_data_names.keys())):
        de = ref_data_names[name]
        operations.append(
            {
                "op": "DATA_CHANGE",
                "legacy_op": "DATA_CHANGE",
                "category": 5,
                "category_name": "Data and cross-pool communication",
                "element": "data",
                "before": de.to_dict(),
                "after": None,
                "detail": f'{de.kind.replace("_", " ")} removed: "{de.name}"',
                "confidence": "high",
                "needs_review": False,
            }
        )

    # Sort operations by Category 1-5, then operation name
    operations.sort(key=lambda op: (op.get("category", 99), op["op"], str(op.get("before") or op.get("after"))))
    return operations


def _change_anchor_sets(
    reference: ProcessModel, variant: ProcessModel, alignment: Alignment, operations: list[dict]
) -> tuple[list[set[str]], dict[str, set[str]]]:
    """Build change-site anchors and the direct reference nodes per site."""
    groups: list[set[str]] = []
    direct: dict[str, set[str]] = {}
    for operation in operations:
        kind = operation["op"]
        legacy_kind = operation.get("legacy_op", kind)
        if kind in {
            "RENAME_NODE",
            "RENAME",
            "NODE_TYPE_CHANGE",
            "CHANGE_TYPE",
            "GATEWAY_TYPE_CHANGE",
            "CHANGE_GATEWAY_TYPE",
            "MARKER_CHANGE",
            "BOUNDARY_CHANGE",
            "DELETE_NODE",
            "DELETE",
        } or legacy_kind in {"RENAME", "CHANGE_TYPE", "CHANGE_GATEWAY_TYPE", "DELETE"}:
            before = operation.get("before") or {}
            a_id = before.get("id")
            if a_id not in reference.nodes:
                continue
            anchors = {a_id}
            for neighbour in reference.predecessors(a_id) + reference.successors(a_id):
                if neighbour in alignment.a_to_b:
                    anchors.add(neighbour)
            groups.append(anchors)
            direct.setdefault(a_id, set()).update(anchors)
        elif kind in {"INSERT_NODE", "INSERT"} or legacy_kind == "INSERT":
            after = operation.get("after") or {}
            b_id = after.get("id")
            anchors: set[str] = set()
            if b_id in variant.nodes:
                for neighbour in variant.predecessors(b_id) + variant.successors(b_id):
                    if neighbour in alignment.b_to_a:
                        anchors.add(alignment.b_to_a[neighbour])
            if anchors:
                groups.append(anchors)
        elif kind in {"INSERT_FLOW", "DELETE_FLOW", "FLOW_CONDITION_CHANGE"}:
            payload = operation.get("before") or operation.get("after") or {}
            ids: set[str] = set()
            for key in ("source_id", "target_id"):
                node_id = payload.get(key)
                if node_id in reference.nodes:
                    ids.add(node_id)
                elif node_id in alignment.b_to_a:
                    ids.add(alignment.b_to_a[node_id])
            if ids:
                groups.append(ids)
    return groups, direct


def _fragment_results(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    decomposition: Decomposition,
    selected: list[Region],
    label_override: dict[str, str],
    options: DiffOptions,
) -> tuple[list[dict], dict[str, dict]]:
    if not selected:
        return [], {}

    results: list[dict] = []
    by_region: dict[str, dict] = {}
    unique = {region.id: region for region in selected}
    matched_variant_nodes = set(alignment.a_to_b.values())
    for region in sorted(unique.values(), key=lambda item: (item.size, item.id)):
        mapped = {alignment.a_to_b[node_id] for node_id in region.nodes if node_id in alignment.a_to_b}
        changed = True
        while changed:
            changed = False
            for node_id in variant.nodes:
                if node_id in mapped or node_id in matched_variant_nodes:
                    continue
                predecessors = variant.predecessors(node_id)
                successors = variant.successors(node_id)
                if any(p in mapped for p in predecessors) and any(s in mapped for s in successors):
                    mapped.add(node_id)
                    changed = True
        report = {
            "id": region.id,
            "entry": reference.nodes[region.entry].display_name
            if region.entry in reference.nodes
            else "(start)",
            "exit": reference.nodes[region.exit].display_name
            if region.exit in reference.nodes
            else "(end)",
            "size": region.size,
            "nodes": [reference.nodes[n].display_name for n in sorted(region.nodes) if n in reference.nodes],
            "node_ids": sorted(region.nodes),
            "status": "checked",
        }
        ref_sub = reference.submodel(region.nodes, name=f"{reference.name} / {region.id}")
        var_sub = variant.submodel(mapped, name=f"{variant.name} / {region.id}")
        if not ref_sub.start_nodes() or not var_sub.start_nodes():
            report["status"] = "skipped"
            report["reason"] = "fragment has no entry point"
        else:
            ref_lts = build_lts(ref_sub, max_states=options.max_states, open_ends=True)
            restricted_map = {
                node_id: label for node_id, label in label_override.items() if node_id in var_sub.nodes
            }
            var_lts = build_lts(
                var_sub, restricted_map, max_states=options.max_states, open_ends=True
            )
            behavior = compare_trace_equivalence(ref_lts, var_lts)
            report.update(
                {
                    "equivalent": behavior["equivalent"],
                    "method": behavior["method"],
                    "counterexample": behavior["counterexample"],
                    "states": {"reference": len(ref_lts.states), "variant": len(var_lts.states)},
                }
            )
        results.append(report)
        by_region[region.id] = report
    return results, by_region


def _pair_behavior(
    pair,
    direct: dict[str, set[str]],
    by_region: dict[str, dict],
    whole: dict,
    decomposition: Decomposition,
) -> dict:
    if pair.a is None or pair.b is None:
        return {"equivalent": False, "scope": "structural"}
    if pair.a not in direct:
        return {"equivalent": True, "scope": "unchanged"}
    region = decomposition.smallest_region_containing(direct[pair.a])
    result = by_region.get(region.id)
    if result and result.get("status") == "checked":
        return {"equivalent": result.get("equivalent"), "scope": region.id}
    return {"equivalent": whole.get("equivalent"), "scope": "whole-model"}


def diff_models(
    reference: ProcessModel, variant: ProcessModel, options: DiffOptions | None = None
) -> Comparison:
    options = options or DiffOptions()
    config = options.alignment_config
    config.use_llm = options.use_llm
    alignment = align(reference, variant, config, llm=options.llm)

    operations = _build_operations(reference, variant, alignment)
    label_override = relabel_map(reference, variant, alignment)

    if operations:
        ref_lts = build_lts(reference, max_states=options.max_states)
        var_lts = build_lts(variant, label_override, max_states=options.max_states)
        behavior = compare_trace_equivalence(ref_lts, var_lts)
        behavior["reference_lts"] = ref_lts.stats()
        behavior["variant_lts"] = var_lts.stats()
        if options.bisimulation:
            behavior["branching_bisimulation"] = weak_bisimilar(ref_lts, var_lts, max_states=6000)
        behavior["trace_samples"] = {
            "reference": enumerate_traces(ref_lts, limit=10, max_traces=8),
            "variant": enumerate_traces(var_lts, limit=10, max_traces=8),
        }
    else:
        behavior = {
            "equivalent": True,
            "inconclusive": False,
            "method": "no edit operations; behaviour is identical by construction",
            "counterexample": None,
            "truncated": False,
            "reference_lts": {},
            "variant_lts": {},
            "trace_samples": {"reference": {"traces": []}, "variant": {"traces": []}},
        }

    decomposition = decompose(reference)
    groups, direct = _change_anchor_sets(reference, variant, alignment, operations)
    selected: dict[str, Region] = {}
    for anchors in groups:
        region = decomposition.smallest_region_containing(anchors)
        selected[region.id] = region
    if groups and not selected:
        selected[decomposition.whole.id] = decomposition.whole
    affected, by_region = _fragment_results(
        reference,
        variant,
        alignment,
        decomposition,
        list(selected.values()),
        label_override,
        options,
    )
    reported_regions = [
        item
        for item in affected
        if not any(
            set(item["node_ids"]) < set(other["node_ids"])
            for other in affected
            if other is not item
        )
    ]

    # Fusion matrix
    pair_verdicts: list[dict] = []
    for pair in alignment.pairs:
        if not pair.matched:
            verdict = "structural_change"
            scope = "element"
            equivalent = False
        else:
            local = _pair_behavior(pair, direct, by_region, behavior, decomposition)
            equivalent = local.get("equivalent")
            scope = local.get("scope", "whole-model")
            if pair.needs_review:
                verdict = "needs_review"
            elif pair.label == "meaning_changed":
                verdict = "semantic_change"
            elif equivalent is True:
                verdict = (
                    "unchanged"
                    if pair.label == "identical"
                    and normalize_label(reference.nodes[pair.a].name)
                    == normalize_label(variant.nodes[pair.b].name)
                    else "non_behavioral_rename"
                )
            elif equivalent is False:
                verdict = "behavioral_change"
            else:
                verdict = "inconclusive"
        pair_verdicts.append(
            {
                "a": reference.nodes[pair.a].display_name if pair.a else None,
                "b": variant.nodes[pair.b].display_name if pair.b else None,
                "label": pair.label,
                "verdict": verdict,
                "behaviour_scope": scope,
                "equivalent": equivalent,
                "needs_review": pair.needs_review,
            }
        )

    operation_counts = Counter(op["op"] for op in operations)
    legacy_counts = Counter(op.get("legacy_op", op["op"]) for op in operations)
    needs_review = sum(1 for pair in alignment.pairs if pair.needs_review)
    has_structural = any(
        op["op"] in {"INSERT_NODE", "DELETE_NODE", "INSERT", "DELETE"} for op in operations
    )
    has_semantic = any(pair.label == "meaning_changed" for pair in alignment.pairs)
    has_rename = (
        operation_counts.get("RENAME_NODE", 0) > 0
        or operation_counts.get("RENAME", 0) > 0
        or operation_counts.get("RENAME_LANE", 0) > 0
        or operation_counts.get("RENAME_SWIMLANE", 0) > 0
    )
    equivalent = behavior.get("equivalent")

    if not operations:
        overall = "identical"
    elif equivalent is False and (has_semantic or needs_review):
        overall = "semantic_and_behavioral_change"
    elif equivalent is False:
        overall = "behavioral_change"
    elif equivalent is None:
        overall = "inconclusive_behavior"
    elif has_semantic:
        overall = "semantic_change"
    elif has_structural:
        overall = "structural_change_non_behavioral"
    elif (
        operation_counts.get("MOVE_LANE", 0) > 0
        or operation_counts.get("CHANGE_SWIMLANE", 0) > 0
    ):
        overall = "non_behavioral_swimlane_change"
    elif has_rename:
        overall = "non_behavioral_rename"
    else:
        overall = "unchanged"

    fusion = {
        "overall": overall,
        "needs_review": needs_review > 0,
        "element_verdicts": pair_verdicts,
        "verdict_counts": dict(Counter(item["verdict"] for item in pair_verdicts)),
        "operation_counts": dict(operation_counts),
        "legacy_operation_counts": dict(legacy_counts),
    }

    return Comparison(
        reference=reference,
        variant=variant,
        alignment=alignment,
        operations=operations,
        behavior=behavior,
        decomposition=decomposition,
        affected_regions=reported_regions,
        fusion=fusion,
        options=options,
    )
