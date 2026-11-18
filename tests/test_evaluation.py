"""Tests for the evaluation harness."""

from __future__ import annotations

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from bpmndiff.cli import main
from bpmndiff.evaluation import (
    Counts,
    evaluate_dataset,
    operation_key,
    write_reports,
)
from bpmndiff.generator import generate_dataset

REPO = Path(__file__).resolve().parents[1]
CONVERTED = (
    REPO
    / "dataset"
    / "BPMN Diagrams Dataset of Functional Requirements"
    / "Converted XPDL"
)

PILOT_FIELDS = [
    "alignment_mode",
    "scenario",
    "change_type",
    "tp",
    "fp",
    "fn",
    "support",
    "precision",
    "recall",
    "f1",
]


class CountsTests(unittest.TestCase):
    def test_precision_recall_and_f1(self):
        counts = Counts(tp=3, fp=1, fn=1)
        self.assertEqual(counts.support, 4)
        self.assertAlmostEqual(counts.precision, 0.75)
        self.assertAlmostEqual(counts.recall, 0.75)
        self.assertAlmostEqual(counts.f1, 0.75)

    def test_empty_ground_truth_counts_as_perfect(self):
        counts = Counts(tp=0, fp=0, fn=0)
        self.assertEqual(counts.precision, 1.0)
        self.assertEqual(counts.recall, 1.0)
        self.assertEqual(counts.f1, 1.0)

    def test_add_accumulates(self):
        total = Counts(tp=1, fp=2, fn=3)
        total.add(Counts(tp=2, fp=3, fn=4))
        self.assertEqual((total.tp, total.fp, total.fn), (3, 5, 7))


class OperationKeyTests(unittest.TestCase):
    def test_flow_endpoints_are_normalized_to_reference_ids(self):
        operation = {
            "op": "INSERT_FLOW",
            "before": None,
            "after": {"source_id": "var_a", "target_id": "var_b"},
        }
        self.assertEqual(
            operation_key(operation, {"var_a": "ref_a", "var_b": "ref_b"}),
            ("INSERT_FLOW", "ref_a", "ref_b"),
        )

    def test_ground_truth_flow_key_matches_detected_flow_key(self):
        truth = {
            "change": {
                "type": "DELETE_FLOW",
                "before": {"source_id": "var_a", "target_id": "var_b"},
                "after": None,
            }
        }
        detected = {
            "op": "DELETE_FLOW",
            "before": {"source_id": "var_a", "target_id": "var_b"},
            "after": None,
        }
        mapping = {"var_a": "ref_a", "var_b": "ref_b"}
        self.assertEqual(
            operation_key(truth, mapping), operation_key(detected, mapping)
        )

    def test_rename_key_uses_reference_side_identity(self):
        operation = {
            "op": "RENAME_NODE",
            "before": {"id": "ref_a", "name": "Old"},
            "after": {"id": "var_a", "name": "New"},
        }
        self.assertEqual(
            operation_key(operation, {"var_a": "ref_a"}), ("RENAME_NODE", "ref_a")
        )


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.dataset = cls.root / "synthetic"
        cls.results = cls.root / "results"
        generate_dataset(CONVERTED, cls.dataset, bases=("57",), seed="eval-test")
        cls.manifest_path = cls.dataset / "manifest.json"
        cls.evaluation = evaluate_dataset(cls.manifest_path)
        cls.paths = write_reports(cls.evaluation, cls.results)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_every_mode_and_scenario_is_reported(self):
        bucket = self.evaluation.counts
        for mode in ("id", "name", "structure", "hybrid"):
            for scenario in ("keep_ids", "new_ids", "all"):
                self.assertIn((mode, scenario), bucket)
        self.assertGreater(
            self.evaluation.row("hybrid", "all", "ALL").support, 0
        )

    def test_keep_ids_is_perfect_for_exact_alignment_modes(self):
        for mode in ("id", "hybrid"):
            counts = self.evaluation.row(mode, "keep_ids", "ALL")
            self.assertEqual(counts.fp, 0)
            self.assertEqual(counts.fn, 0)
            self.assertEqual(counts.f1, 1.0)

    def test_pilot_csv_contract(self):
        with (self.results / "pilot.csv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, PILOT_FIELDS)
            rows = list(reader)

        self.assertTrue(rows)
        keys = {
            (row["alignment_mode"], row["scenario"], row["change_type"])
            for row in rows
        }
        for mode in ("id", "name", "structure", "hybrid"):
            self.assertIn((mode, "all", "ALL"), keys)
        for row in rows:
            for column in ("precision", "recall", "f1"):
                value = float(row[column])
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_reports_are_written(self):
        for key in ("pilot", "pairs", "summary", "errors", "json"):
            self.assertTrue(self.paths[key].is_file(), key)
        payload = json.loads(self.paths["json"].read_text(encoding="utf-8"))
        self.assertIn("hybrid", payload["counts"])

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_dataset(self.manifest_path, modes=("nope",))


class EvaluationCLITests(unittest.TestCase):
    def test_generate_and_evaluate_subcommands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "synthetic"
            results = root / "results"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    main(["generate", "--bases", "57", "--out", str(dataset)]), 0
                )
                self.assertEqual(
                    main(
                        [
                            "evaluate",
                            "--manifest",
                            str(dataset / "manifest.json"),
                            "--out",
                            str(results),
                        ]
                    ),
                    0,
                )
            self.assertTrue((dataset / "manifest.json").is_file())
            self.assertTrue((results / "pilot.csv").is_file())
            self.assertIn("hybrid", output.getvalue())


if __name__ == "__main__":
    unittest.main()
