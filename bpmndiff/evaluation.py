"""Evaluation harness for synthetic mutation datasets.

The harness compares detected operations with ``change-v1`` ground truth and
reports Precision, Recall, and F1 per change type and per alignment mode.  It
normalizes variant IDs back to their reference IDs through the generator's
manifest, so ``INSERT_FLOW`` operations can be compared even when every ID was
regenerated.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .alignment import ALIGNMENT_STRATEGIES, AlignmentConfig
from .diff import DiffOptions, diff_models
from .parsers import load_model

#: Canonical order used in reports when types have equal counts.
CHANGE_TYPES = (
    "INSERT_NODE",
    "DELETE_NODE",
    "RENAME_NODE",
    "NODE_TYPE_CHANGE",
    "MARKER_CHANGE",
    "BOUNDARY_CHANGE",
    "MOVE_LANE",
    "RENAME_LANE",
    "INSERT_LANE",
    "DELETE_LANE",
    "GATEWAY_TYPE_CHANGE",
    "INSERT_FLOW",
    "DELETE_FLOW",
    "FLOW_CONDITION_CHANGE",
    "REORDER",
    "PARALLELIZE",
    "SEQUENTIALIZE",
    "EXTRACT_SUBPROCESS",
    "INLINE_SUBPROCESS",
    "MESSAGE_FLOW_CHANGE",
    "DATA_CHANGE",
)

_NODE_BEFORE_TYPES = {
    "DELETE_NODE",
    "RENAME_NODE",
    "NODE_TYPE_CHANGE",
    "MARKER_CHANGE",
    "BOUNDARY_CHANGE",
    "MOVE_LANE",
    "GATEWAY_TYPE_CHANGE",
    "REORDER",
    "PARALLELIZE",
    "SEQUENTIALIZE",
}
_FLOW_TYPES = {"INSERT_FLOW", "DELETE_FLOW", "FLOW_CONDITION_CHANGE"}
_LANE_TYPES = {"RENAME_LANE", "INSERT_LANE", "DELETE_LANE"}

SCENARIOS = ("keep_ids", "new_ids", "all")


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def support(self) -> int:
        return self.tp + self.fn

    @property
    def precision(self) -> float:
        denominator = self.tp + self.fp
        if denominator:
            return self.tp / denominator
        return 1.0 if self.support == 0 else 0.0

    @property
    def recall(self) -> float:
        denominator = self.support
        return self.tp / denominator if denominator else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def add(self, other: "Counts") -> None:
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn

    def as_row(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "support": self.support,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


@dataclass
class ErrorExample:
    mode: str
    scenario: str
    change_type: str
    direction: str
    variant: str
    base_id: str
    key: tuple


@dataclass
class EvaluationResult:
    manifest: dict[str, Any]
    root: Path | None = None
    counts: dict[tuple[str, str], dict[str, Counts]] = field(default_factory=dict)
    pair_counts: list[dict[str, Any]] = field(default_factory=list)
    errors: list[ErrorExample] = field(default_factory=list)

    def row(self, mode: str, scenario: str, change_type: str) -> Counts:
        return self.counts.get((mode, scenario), {}).get(change_type, Counts())


# ---------------------------------------------------------------------------
# Operation normalization
# ---------------------------------------------------------------------------
def _record_layers(record: dict[str, Any]) -> tuple[str, dict | None, dict | None]:
    if "op" in record:
        return record["op"], record.get("before"), record.get("after")
    change = record["change"]
    return change["type"], change.get("before"), change.get("after")


def operation_key(
    record: dict[str, Any], variant_to_reference: dict[str, str]
) -> tuple:
    """Return a comparable identity for a detected operation or GT record."""
    change_type, before, after = _record_layers(record)

    if change_type == "INSERT_NODE":
        payload = after or {}
        return (change_type, payload.get("id") or payload.get("name", ""))
    if change_type in _NODE_BEFORE_TYPES:
        payload = before or after or {}
        return (change_type, payload.get("id") or payload.get("name", ""))
    if change_type in _FLOW_TYPES:
        if change_type == "INSERT_FLOW":
            payload = after or {}
        else:
            payload = before or after or {}
        source = payload.get("source_id")
        target = payload.get("target_id")
        if source is not None:
            source = variant_to_reference.get(source, source)
        if target is not None:
            target = variant_to_reference.get(target, target)
        if source is None or target is None:
            source = payload.get("source", "")
            target = payload.get("target", "")
        return (change_type, source, target)
    if change_type == "MESSAGE_FLOW_CHANGE":
        payload = after or before or {}
        source = variant_to_reference.get(payload.get("source", ""), payload.get("source", ""))
        target = variant_to_reference.get(payload.get("target", ""), payload.get("target", ""))
        return (change_type, source, target)
    if change_type in _LANE_TYPES:
        payload = before if change_type != "INSERT_LANE" else after
        return (change_type, (payload or {}).get("name", ""))
    if change_type == "DATA_CHANGE":
        payload = after or before or {}
        return (change_type, payload.get("name", ""))
    if change_type in {"EXTRACT_SUBPROCESS", "INLINE_SUBPROCESS"}:
        payload = before or after or {}
        return (change_type, payload.get("subprocess_id") or payload.get("subprocess", ""))
    payload = before or after or {}
    return (change_type, payload.get("id") or payload.get("name", ""))


def _count_keys(records: Iterable[dict[str, Any]], id_map: dict[str, str]) -> Counter:
    return Counter(operation_key(record, id_map) for record in records)


def _compare(predicted: Counter, truth: Counter) -> tuple[Counts, list[tuple], list[tuple]]:
    tp = sum((predicted & truth).values())
    fp_keys = list((predicted - truth).elements())
    fn_keys = list((truth - predicted).elements())
    fp = len(fp_keys)
    fn = len(fn_keys)
    return Counts(tp=tp, fp=fp, fn=fn), fp_keys, fn_keys


def _scenario_for(entry: dict[str, Any]) -> str:
    return "keep_ids" if entry["id_policy"] == "keep" else "new_ids"


def _sorted_types(types: Iterable[str]) -> list[str]:
    present = set(types)
    ordered = [change_type for change_type in CHANGE_TYPES if change_type in present]
    ordered += sorted(present - set(ordered))
    return ordered


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_dataset(
    manifest_path: str | Path,
    *,
    modes: Iterable[str] = ("id", "name", "structure", "hybrid"),
    bisimulation: bool = False,
) -> EvaluationResult:
    manifest_file = Path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    root = manifest_file.parent
    selected_modes = list(modes)
    invalid = set(selected_modes) - set(ALIGNMENT_STRATEGIES)
    if invalid:
        raise ValueError(f"unknown alignment mode(s): {sorted(invalid)}")

    result = EvaluationResult(manifest=manifest, root=root)

    for base in manifest["bases"]:
        reference_path = root / base["reference"]
        reference = load_model(str(reference_path))

        for variant_entry in base["variants"]:
            variant_path = root / variant_entry["path"]
            variant = load_model(str(variant_path))
            truth = json.loads(
                (root / variant_entry["ground_truth"]).read_text(encoding="utf-8")
            )["operations"]
            scenario = _scenario_for(variant_entry)
            variant_to_reference = variant_entry.get("node_map", {})
            truth_keys = _count_keys(truth, variant_to_reference)

            for mode in selected_modes:
                comparison = diff_models(
                    reference,
                    variant,
                    DiffOptions(
                        bisimulation=bisimulation,
                        alignment_config=AlignmentConfig(strategy=mode),
                    ),
                )
                predicted_keys = _count_keys(comparison.operations, variant_to_reference)
                for scope in (scenario, "all"):
                    bucket = result.counts.setdefault((mode, scope), {})
                    for change_type in _sorted_types(
                        {key[0] for key in truth_keys}
                        | {key[0] for key in predicted_keys}
                    ):
                        predicted_type = Counter(
                            {
                                key: value
                                for key, value in predicted_keys.items()
                                if key[0] == change_type
                            }
                        )
                        truth_type = Counter(
                            {
                                key: value
                                for key, value in truth_keys.items()
                                if key[0] == change_type
                            }
                        )
                        counts, fp_keys, fn_keys = _compare(predicted_type, truth_type)
                        bucket.setdefault(change_type, Counts()).add(counts)

                predicted_summary, fp_keys, fn_keys = _compare(predicted_keys, truth_keys)
                result.pair_counts.append(
                    {
                        "base_id": base["base_id"],
                        "variant": variant_entry["variant"],
                        "k": variant_entry["k"],
                        "id_policy": variant_entry["id_policy"],
                        "scenario": scenario,
                        "alignment_mode": mode,
                        **predicted_summary.as_row(),
                        "predicted": sum(predicted_keys.values()),
                        "expected": sum(truth_keys.values()),
                    }
                )

                for direction, keys in (("fp", fp_keys), ("fn", fn_keys)):
                    for key in keys:
                        result.errors.append(
                            ErrorExample(
                                mode=mode,
                                scenario=scenario,
                                change_type=key[0],
                                direction=direction,
                                variant=variant_entry["variant"],
                                base_id=base["base_id"],
                                key=key,
                            )
                        )

    # Aggregate rows for the "all" scenario are already accumulated.
    for (mode, scope), bucket in result.counts.items():
        total = Counts()
        for counts in bucket.values():
            total.add(counts)
        bucket["ALL"] = total
    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _csv_rows(result: EvaluationResult, modes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in modes:
        for scenario in SCENARIOS:
            bucket = result.counts.get((mode, scenario), {})
            if not bucket:
                continue
            change_types = _sorted_types(
                change_type for change_type in bucket if change_type != "ALL"
            )
            for change_type in change_types + ["ALL"]:
                counts = bucket.get(change_type, Counts())
                rows.append(
                    {
                        "alignment_mode": mode,
                        "scenario": scenario,
                        "change_type": change_type,
                        **counts.as_row(),
                    }
                )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def write_reports(
    result: EvaluationResult,
    out_dir: str | Path,
    *,
    modes: Iterable[str] = ("id", "name", "structure", "hybrid"),
) -> dict[str, Path]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    mode_list = list(modes)

    pilot_rows = _csv_rows(result, mode_list)
    pilot_path = output / "pilot.csv"
    _write_csv(
        pilot_path,
        pilot_rows,
        [
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
        ],
    )

    pair_path = output / "pilot_pairs.csv"
    _write_csv(
        pair_path,
        result.pair_counts,
        [
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
        ],
    )

    summary_path = output / "pilot_summary.md"
    summary_path.write_text(_render_summary(result, mode_list), encoding="utf-8")
    errors_path = output / "error_analysis.md"
    errors_path.write_text(_render_error_analysis(result), encoding="utf-8")

    json_path = output / "pilot.json"
    json_path.write_text(
        json.dumps(
            {
                "manifest": str(result.manifest.get("schema", "")),
                "bases": len(result.manifest.get("bases", [])),
                "counts": {
                    mode: {
                        scenario: {
                            change_type: counts.as_row()
                            for change_type, counts in bucket.items()
                        }
                        for scenario, bucket in (
                            (scenario, result.counts.get((mode, scenario), {}))
                            for scenario in SCENARIOS
                        )
                    }
                    for mode in mode_list
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "pilot": pilot_path,
        "pairs": pair_path,
        "summary": summary_path,
        "errors": errors_path,
        "json": json_path,
    }


def _render_summary(result: EvaluationResult, modes: list[str]) -> str:
    lines = [
        "# Evaluation Harness — pilot",
        "",
        f"Dataset: `{result.manifest.get('schema', 'bpmndiff-synthetic-v1')}` · "
        f"{len(result.manifest.get('bases', []))} bases · "
        f"{sum(len(base.get('variants', [])) for base in result.manifest.get('bases', []))} pairs",
        "",
        "Metrics are operation-level: a prediction matches ground truth when the "
        "canonical change type and the element/endpoints identity agree.",
        "",
        "## Overall by mode and scenario",
        "",
        "| Mode | Scenario | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in modes:
        for scenario in SCENARIOS:
            counts = result.row(mode, scenario, "ALL")
            lines.append(
                f"| {mode} | {scenario} | {counts.tp} | {counts.fp} | {counts.fn} | "
                f"{_fmt(counts.precision)} | {_fmt(counts.recall)} | {_fmt(counts.f1)} |"
            )
    lines += [
        "",
        "## Per change type (all scenarios)",
        "",
        "| Change type | Mode | Support | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    types = set()
    for mode in modes:
        types.update(
            change_type
            for change_type in result.counts.get((mode, "all"), {})
            if change_type != "ALL"
        )
    for change_type in _sorted_types(types):
        for mode in modes:
            counts = result.row(mode, "all", change_type)
            if counts.support == 0 and counts.fp == 0:
                continue
            lines.append(
                f"| {change_type} | {mode} | {counts.support} | {counts.tp} | {counts.fp} | "
                f"{counts.fn} | {_fmt(counts.precision)} | {_fmt(counts.recall)} | "
                f"{_fmt(counts.f1)} |"
            )
    lines += [
        "",
        "## ID-regeneration effect",
        "",
        "The `new_ids` scenario regenerates every XML ID while keeping the model "
        "semantics and the injected mutations identical to `keep_ids`. The gap "
        "between the two scenarios isolates identifier dependence.",
        "",
    ]
    for mode in modes:
        keep = result.row(mode, "keep_ids", "ALL")
        churn = result.row(mode, "new_ids", "ALL")
        lines.append(
            f"- **{mode}**: keep {_fmt(keep.f1)} → new IDs {_fmt(churn.f1)} "
            f"(Δ {churn.f1 - keep.f1:+.3f})"
        )
    lines.append("")
    return "\n".join(lines)


def _render_error_analysis(result: EvaluationResult) -> str:
    # Scenarios are aggregated: the same mechanism (for example an unmatched
    # unnamed gateway) fires in both the kept-ID and regenerated-ID variants,
    # so counting them separately would report one mechanism three times.
    patterns: dict[tuple[str, str, str], list[ErrorExample]] = defaultdict(list)
    for error in result.errors:
        patterns[(error.mode, error.change_type, error.direction)].append(error)
    ranked = sorted(
        patterns.items(), key=lambda item: (-len(item[1]), item[0])
    )

    lines = [
        "# Error analysis — three most frequent failure patterns",
        "",
        "Counts aggregate the `keep_ids` and `new_ids` scenarios. Each pattern "
        "lists one concrete generated pair that can be inspected directly in "
        "`dataset/synthetic/`.",
        "",
    ]
    if not ranked:
        lines.append("_No false positives or false negatives were observed._")
        return "\n".join(lines) + "\n"

    for index, ((mode, change_type, direction), examples) in enumerate(
        ranked[:3], start=1
    ):
        # Prefer a kept-ID pair: it isolates the alignment mechanism from the
        # separate identifier-churn effect described in the summary.
        example = min(
            examples,
            key=lambda item: (
                item.scenario != "keep_ids",
                item.base_id,
                item.variant,
            ),
        )
        scenarios = sorted({item.scenario for item in examples})
        root = result.root or Path("dataset/synthetic")
        pair = (root / example.base_id / f"{example.variant}.bpmn").resolve()
        try:
            path = pair.relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            path = str(pair)
        root_cause = _failure_hint(mode, example.scenario, change_type, direction)
        lines += [
            f"## {index}. {direction.upper()} · `{change_type}` · mode `{mode}`",
            "",
            f"- Frequency: **{len(examples)}** occurrences "
            f"({', '.join(f'`{scenario}`' for scenario in scenarios)})",
            f"- Example pair: `{path}`",
            f"- Example identity: `{example.key}`",
            f"- Likely cause: {root_cause}",
            "",
        ]
    return "\n".join(lines)


def _failure_hint(mode: str, scenario: str, change_type: str, direction: str) -> str:
    if mode == "id" and scenario == "new_ids":
        return (
            "ID-only alignment cannot match nodes after a full re-export, so every "
            "node becomes an insert/delete and the real edit is buried."
        )
    if mode == "name" and change_type in {
        "DELETE_NODE",
        "INSERT_NODE",
        "DELETE_FLOW",
        "INSERT_FLOW",
    }:
        return (
            "label-only alignment leaves unnamed gateways and events unmatched, "
            "producing structural false positives around every branch."
        )
    if mode == "structure":
        return (
            "the structural fingerprint is not unique on both sides (parallel "
            "branches or repeated gateway shapes), and the strategy skips every "
            "colour group that is not a singleton."
        )
    if direction == "fn":
        return (
            "the change was too weak for the alignment signal: the mutated node "
            "was not paired with its reference counterpart, or the consequence "
            "flow was not reachable through the matched nodes."
        )
    return (
        "the detector reported an additional operation that the generator did not "
        "inject; inspect the pair to decide whether it is a real consequence or a "
        "false positive."
    )
