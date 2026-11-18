"""Tests for the bpmndiff prototype."""

from __future__ import annotations

import unittest

from bpmndiff.decomposition import decompose
from bpmndiff.diff import DiffOptions, diff_models
from bpmndiff.lts import build_lts, compare_trace_equivalence
from bpmndiff.model import Edge, Node, ProcessModel


def make_model(model_id: str, tasks: list[str], kind: str = "sequence") -> ProcessModel:
    """Build a small model.

    kind="sequence": start -> t1 -> ... -> end
    kind="xor" / "and": start -> gateway -> branches -> join -> end
    """
    model = ProcessModel(id=model_id, name=model_id, source=f"{model_id}.xpdl", fmt="xpdl")
    model.add_node(Node(f"{model_id}-start", "", "start"))
    previous = f"{model_id}-start"
    if kind in {"xor", "and"}:
        model.add_node(Node(f"{model_id}-split", "", kind))
        model.add_edge(Edge(f"{model_id}-e0", previous, f"{model_id}-split"))
        model.add_node(Node(f"{model_id}-join", "", "xor"))
        for index, label in enumerate(tasks):
            task_id = f"{model_id}-task{index}"
            model.add_node(Node(task_id, label, "task"))
            model.add_edge(Edge(f"{model_id}-s{index}", f"{model_id}-split", task_id))
            model.add_edge(Edge(f"{model_id}-j{index}", task_id, f"{model_id}-join"))
        model.add_node(Node(f"{model_id}-end", "", "end"))
        model.add_edge(Edge(f"{model_id}-ej", f"{model_id}-join", f"{model_id}-end"))
        return model

    for index, label in enumerate(tasks):
        task_id = f"{model_id}-task{index}"
        model.add_node(Node(task_id, label, "task"))
        model.add_edge(Edge(f"{model_id}-e{index}", previous, task_id))
        previous = task_id
    model.add_node(Node(f"{model_id}-end", "", "end"))
    model.add_edge(Edge(f"{model_id}-e-end", previous, f"{model_id}-end"))
    return model


class LTSTests(unittest.TestCase):
    def test_sequential_models_equivalent(self):
        a = make_model("a", ["Check form", "Save form"])
        b = make_model("b", ["Check form", "Save form"])
        result = compare_trace_equivalence(build_lts(a), build_lts(b))
        self.assertTrue(result["equivalent"])

    def test_extra_task_is_detected(self):
        a = make_model("a", ["Check form", "Save form"])
        b = make_model("b", ["Check form", "Verify form", "Save form"])
        result = compare_trace_equivalence(build_lts(a), build_lts(b))
        self.assertFalse(result["equivalent"])
        self.assertIn(result["counterexample"]["direction"], {"reference_only", "variant_only"})
        self.assertTrue(result["counterexample"]["trace"])

    def test_xor_vs_and_differ(self):
        a = make_model("a", ["Approve", "Reject"], kind="xor")
        b = make_model("b", ["Approve", "Reject"], kind="and")
        result = compare_trace_equivalence(build_lts(a), build_lts(b))
        self.assertFalse(result["equivalent"])

    def test_relabel_map_restores_equivalence(self):
        a = make_model("a", ["Check form", "Save form"])
        b = make_model("b", ["Verify form", "Store form"])
        result = compare_trace_equivalence(build_lts(a), build_lts(b))
        self.assertFalse(result["equivalent"])
        relabel = {"b-task0": "Check form", "b-task1": "Save form"}
        result = compare_trace_equivalence(build_lts(a), build_lts(b, relabel))
        self.assertTrue(result["equivalent"])

    def test_loop_is_finite_abstraction(self):
        a = make_model("a", ["Fill form"])
        a.add_node(Node("a-gw", "", "xor"))
        a.add_edge(Edge("loop1", "a-task0", "a-gw"))
        a.add_edge(Edge("loop2", "a-gw", "a-task0"))
        a.add_edge(Edge("loop3", "a-gw", "a-end"))
        lts = build_lts(a, max_states=1000)
        self.assertFalse(lts.truncated)
        self.assertTrue(lts.final)


class DecompositionTests(unittest.TestCase):
    def test_regions_include_whole_model(self):
        model = make_model("a", ["One", "Two", "Three"])
        decomposition = decompose(model)
        self.assertGreaterEqual(len(decomposition.regions), 1)
        self.assertEqual(decomposition.whole.nodes, frozenset(model.nodes))
        self.assertEqual(decomposition.whole.parent, None)

    def test_smallest_region_contains_node(self):
        model = make_model("a", ["One", "Two", "Three"])
        decomposition = decompose(model)
        region = decomposition.smallest_region_containing({"a-task1"})
        self.assertIn("a-task1", region.nodes)
        self.assertLessEqual(region.size, len(model.nodes))


class DiffTests(unittest.TestCase):
    @staticmethod
    def _assign_lanes(model: ProcessModel, assignments: dict[str, str]) -> ProcessModel:
        for node in model.nodes.values():
            if node.name in assignments:
                node.lane = assignments[node.name]
                if node.lane not in model.lanes:
                    model.lanes.append(node.lane)
        return model

    def test_rename_only_is_non_behavioural(self):
        a = make_model("a", ["Check form", "Save form"])
        b = make_model("b", ["Check form", "Store form"])
        comparison = diff_models(a, b, DiffOptions(bisimulation=False))
        self.assertTrue(comparison.behavior["equivalent"])
        self.assertTrue(any(op["op"] in {"RENAME", "RENAME_NODE"} for op in comparison.operations))
        self.assertEqual(comparison.fusion["overall"], "non_behavioral_rename")

    def test_swimlane_rename_is_not_reported_as_task_movement(self):
        a = self._assign_lanes(
            make_model("a", ["Review", "Approve"]),
            {"Review": "Operations", "Approve": "Finance"},
        )
        b = self._assign_lanes(
            make_model("b", ["Review", "Approve"]),
            {"Review": "Service", "Approve": "Finance"},
        )

        comparison = diff_models(a, b, DiffOptions(bisimulation=False))

        renames = [op for op in comparison.operations if op["op"] in {"RENAME_SWIMLANE", "RENAME_LANE"}]
        self.assertEqual(len(renames), 1)
        self.assertEqual(renames[0]["before"]["name"], "Operations")
        self.assertEqual(renames[0]["after"]["name"], "Service")
        self.assertFalse(any(op["op"] in {"CHANGE_SWIMLANE", "MOVE_LANE"} for op in comparison.operations))
        self.assertTrue(comparison.behavior["equivalent"])
        self.assertEqual(comparison.fusion["overall"], "non_behavioral_rename")

    def test_task_moved_between_existing_swimlanes(self):
        a = self._assign_lanes(
            make_model("a", ["Review", "Approve"]),
            {"Review": "Operations", "Approve": "Finance"},
        )
        b = self._assign_lanes(
            make_model("b", ["Review", "Approve"]),
            {"Review": "Finance", "Approve": "Finance"},
        )

        comparison = diff_models(a, b, DiffOptions(bisimulation=False))

        changes = [op for op in comparison.operations if op["op"] in {"CHANGE_SWIMLANE", "MOVE_LANE"}]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["before"]["name"], "Review")
        self.assertEqual(changes[0]["before"]["lane"], "Operations")
        self.assertEqual(changes[0]["after"]["lane"], "Finance")
        self.assertFalse(any(op["op"] in {"RENAME_SWIMLANE", "RENAME_LANE"} for op in comparison.operations))
        self.assertTrue(comparison.behavior["equivalent"])
        self.assertEqual(comparison.fusion["overall"], "non_behavioral_swimlane_change")

    def test_insert_operation_and_behaviour_change(self):
        a = make_model("a", ["Check form", "Save form"])
        b = make_model("b", ["Check form", "Verify form", "Save form"])
        comparison = diff_models(a, b, DiffOptions(bisimulation=False))
        self.assertTrue(any(op["op"] in {"INSERT", "INSERT_NODE"} for op in comparison.operations))
        self.assertFalse(comparison.behavior["equivalent"])
        self.assertIn("behavioral_change", comparison.fusion["overall"])

    def test_gateway_type_change(self):
        a = make_model("a", ["Approve", "Reject"], kind="xor")
        b = make_model("b", ["Approve", "Reject"], kind="and")
        comparison = diff_models(a, b, DiffOptions(bisimulation=False))
        ops = [op["op"] for op in comparison.operations]
        self.assertTrue("GATEWAY_TYPE_CHANGE" in ops or "CHANGE_GATEWAY_TYPE" in ops)
        self.assertFalse(comparison.behavior["equivalent"])


if __name__ == "__main__":
    unittest.main()
