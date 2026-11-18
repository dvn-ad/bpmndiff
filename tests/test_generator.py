"""Tests for the deterministic synthetic mutation generator."""

from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from bpmndiff.alignment import AlignmentConfig
from bpmndiff.contract import validate_change_record
from bpmndiff.diff import DiffOptions, diff_models
from bpmndiff.evaluation import operation_key
from bpmndiff.generator import DEFAULT_BASES, GeneratorError, generate_dataset
from bpmndiff.parsers import load_model

REPO = Path(__file__).resolve().parents[1]
CONVERTED = (
    REPO
    / "dataset"
    / "BPMN Diagrams Dataset of Functional Requirements"
    / "Converted XPDL"
)


def _diff_keys(reference_path: Path, variant_path: Path, node_map: dict[str, str]) -> Counter:
    comparison = diff_models(
        load_model(str(reference_path)),
        load_model(str(variant_path)),
        DiffOptions(
            bisimulation=False,
            alignment_config=AlignmentConfig(strategy="hybrid"),
        ),
    )
    return Counter(operation_key(operation, node_map) for operation in comparison.operations)


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.out = cls.root / "dataset"
        cls.manifest = generate_dataset(
            CONVERTED, cls.out, bases=("57",), seed="test-seed"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_manifest_contains_six_variants_per_base(self):
        self.assertEqual(len(self.manifest["bases"]), 1)
        variants = self.manifest["bases"][0]["variants"]
        self.assertEqual(len(variants), 6)
        self.assertEqual({item["k"] for item in variants}, {1, 2, 4})
        self.assertEqual({item["id_policy"] for item in variants}, {"keep", "newids"})

        by_k: dict[int, set[tuple[str, ...]]] = {}
        for item in variants:
            by_k.setdefault(item["k"], set()).add(tuple(item["mutations"]))
        for mutations in by_k.values():
            self.assertEqual(len(mutations), 1, "keep/newids must share mutations")

    def test_ground_truth_is_valid_change_v1_and_covers_mutations(self):
        types: set[str] = set()
        base = self.manifest["bases"][0]
        for variant in base["variants"]:
            payload = json.loads(
                (self.out / variant["ground_truth"]).read_text(encoding="utf-8")
            )
            for record in payload["operations"]:
                validate_change_record(record)
                types.add(record["change"]["type"])

        self.assertTrue(
            {
                "INSERT_NODE",
                "DELETE_NODE",
                "INSERT_FLOW",
                "DELETE_FLOW",
                "FLOW_CONDITION_CHANGE",
                "DATA_CHANGE",
            }
            <= types
        )

    def test_newids_regenerates_every_node_id(self):
        base = self.manifest["bases"][0]
        reference_ids = set(load_model(str(self.out / base["reference"])).nodes)

        for variant in base["variants"]:
            node_map = variant["node_map"]
            if variant["id_policy"] == "keep":
                self.assertEqual(set(node_map), set(node_map.values()))
                self.assertTrue(set(node_map) <= reference_ids)
            else:
                self.assertFalse(set(node_map) & reference_ids)

    def test_hybrid_recovers_the_ground_truth(self):
        base = self.manifest["bases"][0]
        for variant in base["variants"]:
            truth = json.loads(
                (self.out / variant["ground_truth"]).read_text(encoding="utf-8")
            )["operations"]
            node_map = variant["node_map"]
            truth_keys = Counter(operation_key(record, node_map) for record in truth)
            predicted = _diff_keys(
                self.out / base["reference"],
                self.out / variant["path"],
                node_map,
            )
            self.assertEqual(
                predicted,
                truth_keys,
                f"{variant['variant']} hybrid prediction differs from ground truth",
            )

    def test_generation_is_deterministic(self):
        other_out = self.root / "dataset-again"
        generate_dataset(CONVERTED, other_out, bases=("57",), seed="test-seed")
        for relative in (
            "57/reference.bpmn",
            "57/k4_newids.bpmn",
            "57/k4_newids.groundtruth.json",
            "manifest.json",
        ):
            self.assertEqual(
                (self.out / relative).read_bytes(),
                (other_out / relative).read_bytes(),
                f"{relative} is not deterministic",
            )

    def test_unknown_base_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(GeneratorError):
                generate_dataset(CONVERTED, tmp, bases=("does-not-exist",))


class FullPilotTests(unittest.TestCase):
    """Dataset-wide invariants that the per-base unit test cannot see."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.out = cls.root / "dataset"
        cls.manifest = generate_dataset(CONVERTED, cls.out, seed="pilot-test")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_five_bases_and_thirty_pairs(self):
        self.assertEqual([base["base_id"] for base in self.manifest["bases"]], list(DEFAULT_BASES))
        pairs = sum(len(base["variants"]) for base in self.manifest["bases"])
        self.assertEqual(pairs, 30)

    def test_no_identifier_survives_a_full_rewrite(self):
        for base in self.manifest["bases"]:
            reference_ids = set(load_model(str(self.out / base["reference"])).nodes)
            for variant in base["variants"]:
                if variant["id_policy"] != "newids":
                    continue
                self.assertFalse(
                    set(variant["node_map"]) & reference_ids,
                    f"{base['base_id']}/{variant['variant']} leaked reference node IDs",
                )

    def test_references_and_di_resolve(self):
        """Every rewritten reference must point at an element that still exists."""

        for base in self.manifest["bases"]:
            for variant in base["variants"]:
                tree = ET.parse(self.out / variant["path"])
                ids = {
                    element.get("id")
                    for element in tree.getroot().iter()
                    if element.get("id")
                }
                for element in tree.getroot().iter():
                    tag = element.tag.rsplit("}", 1)[-1]
                    for attribute, value in element.attrib.items():
                        if (
                            attribute.endswith("Ref") or attribute == "bpmnElement"
                        ) and value:
                            self.assertIn(
                                value,
                                ids,
                                f"{base['base_id']}/{variant['variant']} "
                                f"dangling {tag}.{attribute}",
                            )
                    text = (element.text or "").strip()
                    if text and (
                        tag in {"incoming", "outgoing", "flowNodeRef"}
                        or tag.endswith("Ref")
                        or tag.endswith("Refs")
                    ):
                        self.assertIn(
                            text,
                            ids,
                            f"{base['base_id']}/{variant['variant']} "
                            f"dangling {tag} text",
                        )

    def test_hybrid_recovers_each_pair(self):
        for base in self.manifest["bases"]:
            for variant in base["variants"]:
                truth = json.loads(
                    (self.out / variant["ground_truth"]).read_text(encoding="utf-8")
                )["operations"]
                node_map = variant["node_map"]
                truth_keys = Counter(
                    operation_key(record, node_map) for record in truth
                )
                predicted = _diff_keys(
                    self.out / base["reference"],
                    self.out / variant["path"],
                    node_map,
                )
                self.assertEqual(
                    predicted,
                    truth_keys,
                    f"{base['base_id']}/{variant['variant']} differs from ground truth",
                )


if __name__ == "__main__":
    unittest.main()
