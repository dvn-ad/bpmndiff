"""Regression tests for the Cashier BPMN comparison."""

from __future__ import annotations

import unittest
from pathlib import Path

from bpmndiff.diff import DiffOptions, diff_models
from bpmndiff.model import Edge, Node, ProcessModel
from bpmndiff.parsers import load_model


class CashierRegressionTests(unittest.TestCase):
    def test_invisible_task_aligns_to_renamed_message_task(self):
        dataset = Path(__file__).resolve().parents[1] / "dataset"
        reference = load_model(str(dataset / "Cashier 1.bpmn"))
        variant = load_model(str(dataset / "Cashier 2.bpmn"))

        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))

        rename_ops = [
            operation
            for operation in comparison.operations
            if operation["op"] == "RENAME_NODE"
            and operation["before"]["name"] == "Invisible Task"
            and operation["after"]["name"] == "Displays the message data not found"
        ]
        self.assertEqual(len(rename_ops), 1)
        self.assertEqual(rename_ops[0]["label"], "meaning_changed")
        self.assertEqual(rename_ops[0]["subtype"], "meaning_changed")
        self.assertFalse(rename_ops[0]["is_synonym"])
        self.assertFalse(
            any(
                operation["op"] in {"DELETE_NODE", "INSERT_NODE"}
                and (operation.get("before") or operation.get("after"))["name"]
                in {"Invisible Task", "Displays the message data not found"}
                for operation in comparison.operations
            )
        )

    def test_placeholder_is_not_aligned_across_different_structure(self):
        reference = ProcessModel("reference", "Reference")
        for node in (
            Node("start", "Start", "start"),
            Node("placeholder", "Invisible Task", "task"),
            Node("end", "End", "end"),
        ):
            reference.add_node(node)
        reference.add_edge(Edge("r1", "start", "placeholder"))
        reference.add_edge(Edge("r2", "placeholder", "end"))

        variant = ProcessModel("variant", "Variant")
        for node in (
            Node("start", "Start", "start"),
            Node("message", "Displays the message data not found", "task"),
            Node("other", "Continue processing", "task"),
            Node("end", "End", "end"),
        ):
            variant.add_node(node)
        variant.add_edge(Edge("v1", "start", "message"))
        variant.add_edge(Edge("v2", "message", "other"))
        variant.add_edge(Edge("v3", "other", "end"))

        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))

        self.assertTrue(
            any(
                operation["op"] == "DELETE_NODE"
                and operation["before"]["name"] == "Invisible Task"
                for operation in comparison.operations
            )
        )
        self.assertTrue(
            any(
                operation["op"] == "INSERT_NODE"
                and operation["after"]["name"] == "Displays the message data not found"
                for operation in comparison.operations
            )
        )
        self.assertFalse(any(operation["op"] == "RENAME_NODE" for operation in comparison.operations))

    def test_hybrid_matches_lexically_related_task_by_unique_context(self):
        dataset = Path(__file__).resolve().parents[1] / "dataset"
        reference = load_model(str(dataset / "Cashier 1.bpmn"))
        variant = load_model(str(dataset / "Cashier 3.bpmn"))

        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))
        renames = {
            (operation["before"]["name"], operation["after"]["name"])
            for operation in comparison.operations
            if operation["op"] == "RENAME_NODE"
        }

        self.assertIn(
            ("Enters Down Payment information", "Enters the receipt number"),
            renames,
        )
        unmatched_task_names = {
            operation["before"]["name"]
            for operation in comparison.operations
            if operation["op"] == "DELETE_NODE"
        } | {
            operation["after"]["name"]
            for operation in comparison.operations
            if operation["op"] == "INSERT_NODE"
        }
        self.assertEqual(
            unmatched_task_names,
            {"Saves the Down Payment information", "Prints the receipt"},
        )


if __name__ == "__main__":
    unittest.main()
