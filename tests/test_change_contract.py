"""Tests for the standardized change/evidence output contract."""

from __future__ import annotations

import copy
import unittest

from bpmndiff.alignment import Alignment
from bpmndiff.contract import (
    ComparisonInvariantError,
    assert_diff_invariants,
    validate_change_record,
)
from bpmndiff.diff import DiffOptions, diff_models
from bpmndiff.model import Edge, Node, ProcessModel


def _renamed_processes() -> tuple[ProcessModel, ProcessModel]:
    reference = ProcessModel("reference", "Reference")
    variant = ProcessModel("variant", "Variant")
    for model, task_name in (
        (reference, "Save form"),
        (variant, "Store form"),
    ):
        model.add_node(Node(f"{model.id}-start", "Start", "start"))
        model.add_node(Node(f"{model.id}-task", task_name, "task"))
        model.add_node(Node(f"{model.id}-end", "End", "end"))
        model.add_edge(Edge(f"{model.id}-e1", f"{model.id}-start", f"{model.id}-task"))
        model.add_edge(Edge(f"{model.id}-e2", f"{model.id}-task", f"{model.id}-end"))
    return reference, variant


class ChangeContractTests(unittest.TestCase):
    def test_change_and_evidence_layers_are_emitted(self):
        reference, variant = _renamed_processes()
        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))
        record = next(op for op in comparison.operations if op["op"] == "RENAME_NODE")
        serialized = comparison.to_dict()

        self.assertEqual(serialized["change_schema_version"], "change-v1")
        self.assertEqual(record["schema_version"], "change-v1")
        self.assertEqual(record["change"]["type"], "RENAME_NODE")
        self.assertEqual(record["change"]["legacy_type"], "RENAME")
        self.assertEqual(record["change"]["before"], record["before"])
        self.assertEqual(record["evidence"]["alignment"][0]["label"], "synonym")
        self.assertTrue(record["evidence"]["structural_context"])
        validate_change_record(record)

    def test_invalid_change_type_is_rejected_by_schema(self):
        reference, variant = _renamed_processes()
        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))
        record = copy.deepcopy(next(op for op in comparison.operations if op["op"] == "RENAME_NODE"))
        record["change"]["type"] = "UNSUPPORTED_CHANGE"

        with self.assertRaises(ComparisonInvariantError):
            validate_change_record(record)

    def test_legacy_mirror_mismatch_fails_runtime_invariants(self):
        reference, variant = _renamed_processes()
        comparison = diff_models(reference, variant, DiffOptions(bisimulation=False))
        operations = copy.deepcopy(comparison.operations)
        rename = next(op for op in operations if op["op"] == "RENAME_NODE")
        rename["op"] = "DELETE_NODE"

        with self.assertRaises(ComparisonInvariantError):
            assert_diff_invariants(reference, variant, comparison.alignment, operations)


if __name__ == "__main__":
    unittest.main()
