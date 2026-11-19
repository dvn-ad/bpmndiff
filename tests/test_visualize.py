"""Tests for the optional pandas/matplotlib visualization layer."""

from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

from bpmndiff.cli import main

HAS_VIZ = all(
    importlib.util.find_spec(module) is not None for module in ("pandas", "matplotlib")
)

if HAS_VIZ:
    from bpmndiff.visualize import (
        VisualizationError,
        build_figures,
    )

MODES = ("id", "name", "structure", "hybrid")
SCENARIOS = ("keep_ids", "new_ids", "all")
TYPES = ("INSERT_NODE", "RENAME_NODE")

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
PAIR_FIELDS = [
    "base_id",
    "variant",
    "k",
    "id_policy",
    "scenario",
    "alignment_mode",
    "tp",
    "fp",
    "fn",
    "support",
    "precision",
    "recall",
    "f1",
    "predicted",
    "expected",
]

PAIR_ROWS = (
    # variant, mode, f1, predicted
    ("k1_keep", "id", 1.0, 2),
    ("k1_keep", "name", 0.5, 5),
    ("k1_keep", "structure", 0.0, 3),
    ("k1_keep", "hybrid", 1.0, 2),
    ("k2_keep", "id", 0.8, 3),
    ("k2_keep", "name", 0.6, 2),
    ("k2_keep", "structure", 0.2, 6),
    ("k2_keep", "hybrid", 1.0, 3),
    ("k4_keep", "id", 0.5, 5),
    ("k4_keep", "name", 0.4, 8),
    ("k4_keep", "structure", 0.1, 4),
    ("k4_keep", "hybrid", 1.0, 4),
    ("k4_newids", "id", 0.1, 8),
    ("k4_newids", "name", 0.3, 6),
    ("k4_newids", "structure", 0.1, 5),
    ("k4_newids", "hybrid", 1.0, 3),
)


def _write_fixture(results: Path) -> None:
    results.mkdir(parents=True, exist_ok=True)
    with (results / "pilot.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=PILOT_FIELDS)
        writer.writeheader()
        for mode_index, mode in enumerate(MODES):
            for scenario_index, scenario in enumerate(SCENARIOS):
                base = 1.0 - 0.2 * mode_index - 0.05 * scenario_index
                for change_type in ("ALL", *TYPES):
                    score = max(0.0, base if change_type == "ALL" else base - 0.15)
                    writer.writerow(
                        {
                            "alignment_mode": mode,
                            "scenario": scenario,
                            "change_type": change_type,
                            "tp": 3,
                            "fp": mode_index + scenario_index,
                            "fn": mode_index,
                            "support": 4,
                            "precision": round(max(0.0, score - 0.1), 4),
                            "recall": round(score, 4),
                            "f1": round(score, 4),
                        }
                    )

    with (results / "pilot_pairs.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        for variant, mode, f1, predicted in PAIR_ROWS:
            writer.writerow(
                {
                    "base_id": "99",
                    "variant": variant,
                    "k": 1,
                    "id_policy": "keep",
                    "scenario": "keep_ids",
                    "alignment_mode": mode,
                    "tp": 1,
                    "fp": 1,
                    "fn": 1,
                    "support": 2,
                    "precision": f1,
                    "recall": f1,
                    "f1": f1,
                    "predicted": predicted,
                    "expected": 4,
                }
            )


@unittest.skipUnless(HAS_VIZ, "pandas/matplotlib not installed; install .[viz]")
class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.results = cls.root / "results"
        _write_fixture(cls.results)
        cls.out = cls.root / "figures"
        cls.figures = build_figures(cls.results, cls.out)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_all_figures_are_valid_png(self):
        for name in (
            "overall",
            "type_heatmap",
            "id_churn",
            "pair_heatmap",
            "distribution",
            "correlation",
        ):
            path = self.figures.files[name]
            self.assertTrue(path.is_file(), name)
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", name)
            self.assertGreater(path.stat().st_size, 5000, name)

    def test_correlation_csv(self):
        path = self.figures.files["correlation_csv"]
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(rows)
        metrics = {row["metric"] for row in rows}
        self.assertEqual(metrics, {"pair_f1", "predicted_operations"})

        by_metric: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_metric.setdefault(row["metric"], []).append(row)
        # Hybrid F1 is constant in the fixture, so only three modes correlate.
        self.assertEqual(len(by_metric["pair_f1"]), 9)
        self.assertEqual(len(by_metric["predicted_operations"]), 16)
        for row in by_metric["pair_f1"]:
            if row["mode_a"] == row["mode_b"]:
                self.assertAlmostEqual(float(row["pearson_r"]), 1.0)

    def test_build_is_deterministic(self):
        other = self.root / "figures-again"
        build_figures(self.results, other)
        self.assertEqual(
            self.figures.files["correlation_csv"].read_bytes(),
            (other / "mode_correlation.csv").read_bytes(),
        )

    def test_missing_csv_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VisualizationError):
                build_figures(tmp, Path(tmp) / "figures")

    def test_cli_visualize(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(
                [
                    "visualize",
                    "--results",
                    str(self.results),
                    "--out",
                    str(self.root / "cli-figures"),
                ]
            )
        self.assertEqual(status, 0)
        self.assertIn("mode_overall.png", output.getvalue())


if __name__ == "__main__":
    unittest.main()
