"""Tests for the selectable node-alignment strategies."""

from __future__ import annotations

import unittest

from bpmndiff.alignment import AlignmentConfig, align
from bpmndiff.model import Edge, Node, ProcessModel


def _single_task(model_id: str, task_id: str, task_name: str) -> ProcessModel:
    model = ProcessModel(model_id, model_id)
    start_id, end_id = f"{model_id}-start", f"{model_id}-end"
    model.add_node(Node(start_id, "Start", "start"))
    model.add_node(Node(task_id, task_name, "task"))
    model.add_node(Node(end_id, "End", "end"))
    model.add_edge(Edge(f"{model_id}-in", start_id, task_id))
    model.add_edge(Edge(f"{model_id}-out", task_id, end_id))
    return model


def _parallel_tasks(model_id: str, names: tuple[str, str]) -> ProcessModel:
    model = ProcessModel(model_id, model_id)
    for node in (
        Node(f"{model_id}-start", "Start", "start"),
        Node(f"{model_id}-split", "", "xor"),
        Node(f"{model_id}-left", names[0], "task"),
        Node(f"{model_id}-right", names[1], "task"),
        Node(f"{model_id}-join", "", "xor"),
        Node(f"{model_id}-end", "End", "end"),
    ):
        model.add_node(node)
    for index, (source, target) in enumerate(
        (
            (f"{model_id}-start", f"{model_id}-split"),
            (f"{model_id}-split", f"{model_id}-left"),
            (f"{model_id}-split", f"{model_id}-right"),
            (f"{model_id}-left", f"{model_id}-join"),
            (f"{model_id}-right", f"{model_id}-join"),
            (f"{model_id}-join", f"{model_id}-end"),
        )
    ):
        model.add_edge(Edge(f"{model_id}-edge-{index}", source, target))
    return model


class AlignmentStrategyTests(unittest.TestCase):
    def test_id_strategy_uses_ids_not_names(self):
        reference = _single_task("a", "shared-task", "Approve claim")
        variant = _single_task("b", "shared-task", "Reject claim")

        result = align(reference, variant, AlignmentConfig(strategy="id"))

        self.assertEqual(result.a_to_b, {"shared-task": "shared-task"})
        self.assertEqual(result.pair_of_a["shared-task"].label, "meaning_changed")

    def test_name_strategy_uses_labels_not_ids(self):
        reference = _single_task("a", "reference-task", "Approve claim")
        variant = _single_task("b", "variant-task", "Approve claim")

        result = align(reference, variant, AlignmentConfig(strategy="name"))

        self.assertEqual(result.a_to_b["reference-task"], "variant-task")
        self.assertEqual(result.a_to_b["a-start"], "b-start")
        self.assertEqual(result.a_to_b["a-end"], "b-end")

    def test_structure_strategy_ignores_ids_and_labels(self):
        reference = _single_task("a", "reference-task", "Approve claim")
        variant = _single_task("b", "variant-task", "Display receipt")

        result = align(reference, variant, AlignmentConfig(strategy="structure"))

        self.assertEqual(result.a_to_b["a-start"], "b-start")
        self.assertEqual(result.a_to_b["reference-task"], "variant-task")
        self.assertEqual(result.a_to_b["a-end"], "b-end")
        self.assertEqual(result.pair_of_a["reference-task"].label, "meaning_changed")
        self.assertIn("structural context", result.pair_of_a["reference-task"].reason)

    def test_structure_strategy_leaves_symmetric_nodes_unmatched(self):
        reference = _parallel_tasks("a", ("Approve", "Reject"))
        variant = _parallel_tasks("b", ("Accept", "Decline"))

        result = align(reference, variant, AlignmentConfig(strategy="structure"))

        self.assertNotIn("a-left", result.a_to_b)
        self.assertNotIn("a-right", result.a_to_b)
        self.assertIn("a-left", {pair.a for pair in result.unmatched_a})
        self.assertIn("a-right", {pair.a for pair in result.unmatched_a})

    def test_hybrid_remains_the_default_and_invalid_strategy_is_rejected(self):
        reference = _single_task("a", "a-task", "Save form")
        variant = _single_task("b", "b-task", "Store form")

        default_result = align(reference, variant)
        explicit_result = align(reference, variant, AlignmentConfig(strategy="hybrid"))

        self.assertEqual(default_result.a_to_b, explicit_result.a_to_b)
        self.assertEqual(default_result.pair_of_a["a-task"].label, "synonym")
        with self.assertRaises(ValueError):
            AlignmentConfig(strategy="unknown")

    def test_hybrid_uses_exact_ids_before_name_and_structure(self):
        reference = _single_task("a", "t", "Completely old wording")
        variant = ProcessModel("b", "b")
        for node in (
            Node("b-start", "Start", "start"),
            Node("t", "Unrelated new wording", "task"),
            Node("b-extra", "Additional step", "task"),
            Node("b-end", "End", "end"),
        ):
            variant.add_node(node)
        for index, (source, target) in enumerate(
            (
                ("b-start", "t"),
                ("t", "b-extra"),
                ("b-extra", "b-end"),
            )
        ):
            variant.add_edge(Edge(f"b-edge-{index}", source, target))

        result = align(reference, variant, AlignmentConfig(strategy="hybrid"))

        self.assertEqual(result.a_to_b["t"], "t")
        self.assertEqual(result.pair_of_a["t"].label, "meaning_changed")

    def test_hybrid_uses_unique_aligned_context_for_renamed_tasks(self):
        reference = _single_task("a", "reference-task", "Enters Down Payment information")
        variant = _single_task("b", "variant-task", "Enters the receipt number")

        result = align(reference, variant, AlignmentConfig(strategy="hybrid"))

        self.assertEqual(result.a_to_b["reference-task"], "variant-task")
        self.assertEqual(result.pair_of_a["reference-task"].label, "meaning_changed")
        self.assertIn("structural context", result.pair_of_a["reference-task"].reason)

    def test_hybrid_leaves_symmetric_renamed_tasks_unmatched(self):
        reference = _parallel_tasks("a", ("Approve claim", "Reject claim"))
        variant = _parallel_tasks("b", ("Accept request", "Decline request"))

        result = align(reference, variant, AlignmentConfig(strategy="hybrid"))

        self.assertNotIn("a-left", result.a_to_b)
        self.assertNotIn("a-right", result.a_to_b)


if __name__ == "__main__":
    unittest.main()
