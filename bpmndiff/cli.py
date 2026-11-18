"""Command-line interface for the bpmndiff prototype."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .alignment import ALIGNMENT_STRATEGIES, AlignmentConfig
from .diff import DiffOptions, diff_models
from .evaluation import evaluate_dataset, write_reports
from .generator import DEFAULT_BASES, generate_dataset
from .llm import get_adjudicator
from .parsers import ParseError, load_model
from .report import render_json, render_markdown, render_text


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--process", metavar="ID|NAME", help="select a specific process inside the file")
    parser.add_argument("--max-states", type=int, default=20000, help="LTS state exploration cap (default: 20000)")
    parser.add_argument("--no-bisimulation", action="store_true", help="skip the partition-refinement check")
    parser.add_argument("--llm", action="store_true", help="enable optional LLM adjudication for ambiguous pairs")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.45,
        help="minimum label similarity for a match (default: 0.45)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bpmndiff",
        description="Compare BPMN/XPDL process models: alignment, edit script and behavioural checks.",
    )
    parser.add_argument("files", nargs=2, help="two .bpmn/.xpdl/.xml files")
    parser.add_argument(
        "--alignment-mode",
        "--strategy",
        choices=sorted(ALIGNMENT_STRATEGIES),
        default=None,
        help="node matching strategy for pairwise comparison (default: hybrid)",
    )
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="report format (default: text)")
    parser.add_argument("--out", metavar="PATH", help="write the report to a file instead of stdout")
    parser.add_argument("--fail-on-change", action="store_true", help="exit with status 1 when models differ behaviourally")
    _add_common_options(parser)
    parser.add_argument("--version", action="version", version=f"bpmndiff {__version__}")
    return parser


def _options(args: argparse.Namespace) -> DiffOptions:
    strategy = args.alignment_mode
    config = AlignmentConfig(
        match_threshold=args.threshold,
        strategy=strategy or "hybrid",
    )
    adjudicator = get_adjudicator(args.llm)
    return DiffOptions(
        max_states=args.max_states,
        bisimulation=not args.no_bisimulation,
        use_llm=bool(adjudicator),
        llm=adjudicator,
        alignment_config=config,
    )


def _run(args: argparse.Namespace) -> tuple[dict, bool]:
    if len(args.files) != 2:
        raise SystemExit("pairwise comparison requires exactly two files")

    models = [load_model(path, args.process) for path in args.files]
    options = _options(args)
    comparison = diff_models(models[0], models[1], options)
    result = comparison.to_dict()
    result["mode"] = "A"
    behavior_changed = comparison.behavior.get("equivalent") is False
    return result, behavior_changed


def _write(path: str, content: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _emit(result: dict, args: argparse.Namespace) -> None:
    fmt = args.format
    if args.out and fmt == "text":
        ext = os.path.splitext(args.out)[1].lower()
        if ext in {".md", ".markdown"}:
            fmt = "markdown"
        elif ext == ".json":
            fmt = "json"

    if fmt == "json":
        content = render_json(result)
    elif fmt == "markdown":
        content = render_markdown(result)
    else:
        content = render_text(result)

    if args.out:
        _write(args.out, content)
        print(f"report written to {args.out}")
    else:
        print(content)


# ---------------------------------------------------------------------------
# Demo on the Mini Hospital dataset
# ---------------------------------------------------------------------------
def _dataset_root() -> Path:
    env = os.environ.get("BPMNDIFF_DATASET")
    candidates = []
    if env:
        candidates.append(Path(env))
    repo = Path(__file__).resolve().parent.parent
    candidates.append(repo / "BPMN Diagrams Dataset of Functional Requirements" / "XPDL Dataset")
    candidates.append(Path.cwd() / "BPMN Diagrams Dataset of Functional Requirements" / "XPDL Dataset")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise SystemExit(
        "dataset not found; pass --dataset or set BPMNDIFF_DATASET to the XPDL dataset folder"
    )


def _find_model(root: Path, prefix: str) -> Path:
    matches = sorted(root.glob(f"{prefix}.*"))
    if not matches:
        raise FileNotFoundError(f"no dataset folder starting with {prefix!r}")
    for folder in matches:
        xpdl = sorted(folder.glob("*.xpdl"))
        if xpdl:
            return xpdl[0]
        bpmn = sorted(folder.glob("*.bpmn"))
        if bpmn:
            return bpmn[0]
    raise FileNotFoundError(f"no model file in folder {matches[0]}")


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")[:60]


def run_demo(dataset: Path | None = None, out_dir: Path | None = None) -> int:
    root = dataset or _dataset_root()
    output = out_dir or (Path.cwd() / "reports")
    output.mkdir(parents=True, exist_ok=True)

    tax_dir = Path(__file__).resolve().parent.parent / "dataset" / "taxonomy_variants"
    taxonomy_scenarios = []
    if tax_dir.is_dir():
        taxonomy_scenarios = [
            (
                "Taxonomy 1: Steps (Tasks and Events)",
                [tax_dir / "scenario1_steps_v1.bpmn", tax_dir / "scenario1_steps_v2.bpmn"],
                "Covers INSERT_NODE, DELETE_NODE, RENAME_NODE, NODE_TYPE_CHANGE, MARKER_CHANGE, BOUNDARY_CHANGE",
            ),
            (
                "Taxonomy 2: Actors (Lanes and Pools)",
                [tax_dir / "scenario2_actors_v1.bpmn", tax_dir / "scenario2_actors_v2.bpmn"],
                "Covers MOVE_LANE, RENAME_LANE, INSERT_LANE, DELETE_LANE",
            ),
            (
                "Taxonomy 3: Sequence, Flow, and Branching",
                [tax_dir / "scenario3_flows_v1.bpmn", tax_dir / "scenario3_flows_v2.bpmn"],
                "Covers REORDER, GATEWAY_TYPE_CHANGE, INSERT_FLOW, DELETE_FLOW, FLOW_CONDITION_CHANGE, PARALLELIZE",
            ),
            (
                "Taxonomy 4: Sub-process Structure",
                [tax_dir / "scenario4_subprocesses_v1.bpmn", tax_dir / "scenario4_subprocesses_v2.bpmn"],
                "Covers EXTRACT_SUBPROCESS, INLINE_SUBPROCESS",
            ),
            (
                "Taxonomy 5: Data and Cross-Pool Communication",
                [tax_dir / "scenario5_data_and_messages_v1.bpmn", tax_dir / "scenario5_data_and_messages_v2.bpmn"],
                "Covers MESSAGE_FLOW_CHANGE, DATA_CHANGE",
            ),
        ]

    scenarios = taxonomy_scenarios + [
        (
            "Old vs. new patient registration",
            ["51", "52"],
            "51 vs 52 · old patient vs general new patient registration",
        ),
        (
            "General vs. corporate new patient registration",
            ["52", "53"],
            "52 vs 53 · general vs corporate new patient registration",
        ),
        (
            "General vs. corporate inpatient registration",
            ["54", "55"],
            "54 vs 55 · general vs corporate inpatient registration",
        ),
        (
            "General patient cashier vs. down payment",
            ["58", "59"],
            "58 vs 59 · general patient cashier vs down payment",
        ),
    ]

    options = DiffOptions(max_states=20000, bisimulation=True)
    summary: list[dict] = []
    markdown_parts = [
        "# bpmndiff demo report",
        "",
        f"Dataset: `{root}`",
        "",
        "| Scenario | Mode | Verdict | Trace equivalent | Details |",
        "|---|---|---|---|---|",
    ]

    for index, (title, prefixes, description) in enumerate(scenarios, start=1):
        try:
            if prefixes and isinstance(prefixes[0], Path):
                paths = prefixes
            else:
                paths = [_find_model(root, prefix) for prefix in prefixes]
            models = [load_model(str(path)) for path in paths]
            result = diff_models(models[0], models[1], options).to_dict()
            result["mode"] = "A"
            verdict = result["fusion"]["overall"]
            equiv = result["behavior"]["equivalent"]
            details = f"{len(result['operations'])} operations"

            slug = f"{index:02d}_A_{_slug(title)}"
            _write(str(output / f"{slug}.json"), render_json(result))
            _write(str(output / f"{slug}.md"), render_markdown(result))

            summary.append(
                {
                    "scenario": title,
                    "mode": "A",
                    "description": description,
                    "models": [model.name for model in models],
                    "verdict": verdict,
                    "trace_equivalent": equiv,
                    "details": details,
                    "report": f"{slug}.md",
                }
            )
            markdown_parts.append(
                f"| {title} | A | {verdict} | {'yes' if equiv else 'no'} | {details} |"
            )
            print(
                f"[{index}/{len(scenarios)}] {title}: {verdict} "
                f"({'equivalent' if equiv else 'NOT equivalent'})"
            )
        except (ParseError, FileNotFoundError, KeyError, ValueError) as exc:
            print(f"[{index}/{len(scenarios)}] {title}: FAILED - {exc}", file=sys.stderr)
            summary.append({"scenario": title, "mode": "A", "error": str(exc)})
            markdown_parts.append(f"| {title} | A | error | - | {exc} |")

    markdown_parts += [
        "",
        "## Scenario details",
        "",
    ]
    for item in summary:
        if "report" not in item:
            continue
        markdown_parts.append(f"### {item['scenario']}\n")
        markdown_parts.append(f"- Mode: {item['mode']}")
        markdown_parts.append(f"- Models: {', '.join(item['models'])}")
        markdown_parts.append(f"- Verdict: **{item['verdict']}**")
        markdown_parts.append(f"- Trace equivalent: {item['trace_equivalent']}")
        markdown_parts.append(f"- Details: {item['details']}")
        markdown_parts.append(f"- Report: [{item['report']}]({item['report']})\n")

    _write(str(output / "demo_report.md"), "\n".join(markdown_parts))
    _write(str(output / "demo_summary.json"), json.dumps(summary, indent=2))
    print(f"demo reports written to {output}")
    return 0


def _build_demo_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bpmndiff demo", description="Run the Mini Hospital dataset demo.")
    parser.add_argument("--dataset", help="path to the XPDL dataset folder")
    parser.add_argument("--out", default="reports", help="output directory (default: reports)")
    return parser


# ---------------------------------------------------------------------------
# Synthetic dataset generation and evaluation
# ---------------------------------------------------------------------------
def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_converted_dataset() -> Path:
    return (
        _repo_root()
        / "dataset"
        / "BPMN Diagrams Dataset of Functional Requirements"
        / "Converted XPDL"
    )


def _build_generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bpmndiff generate",
        description="Generate the synthetic k=1/2/4 mutation dataset with ground truth.",
    )
    parser.add_argument(
        "--dataset",
        default=str(_default_converted_dataset()),
        help="folder with the base .bpmn diagrams (default: Converted XPDL)",
    )
    parser.add_argument(
        "--out",
        default=str(_repo_root() / "dataset" / "synthetic"),
        help="output dataset folder (default: dataset/synthetic)",
    )
    parser.add_argument(
        "--bases",
        default=",".join(DEFAULT_BASES),
        help="comma-separated base diagram IDs (default: 56,57,58,63,65)",
    )
    parser.add_argument("--seed", default="bpmndiff", help="deterministic ID-rewrite salt")
    return parser


def run_generate(args: argparse.Namespace) -> int:
    bases = [base.strip() for base in args.bases.split(",") if base.strip()]
    manifest = generate_dataset(
        Path(args.dataset),
        Path(args.out),
        bases=bases,
        seed=args.seed,
    )
    pairs = sum(len(base["variants"]) for base in manifest["bases"])
    print(
        f"generated {pairs} pairs from {len(manifest['bases'])} bases "
        f"in {args.out}"
    )
    print(f"manifest: {Path(args.out) / 'manifest.json'}")
    return 0


def _build_evaluate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bpmndiff evaluate",
        description="Evaluate detected changes against synthetic ground truth.",
    )
    parser.add_argument(
        "--manifest",
        default=str(_repo_root() / "dataset" / "synthetic" / "manifest.json"),
        help="synthetic dataset manifest (default: dataset/synthetic/manifest.json)",
    )
    parser.add_argument(
        "--out",
        default=str(_repo_root() / "results"),
        help="results folder (default: results)",
    )
    parser.add_argument(
        "--modes",
        default="id,name,structure,hybrid",
        help="comma-separated alignment modes (default: id,name,structure,hybrid)",
    )
    parser.add_argument(
        "--bisimulation",
        action="store_true",
        help="also run the partition-refinement check (slower)",
    )
    return parser


def run_evaluate(args: argparse.Namespace) -> int:
    modes = [mode.strip() for mode in args.modes.split(",") if mode.strip()]
    result = evaluate_dataset(
        args.manifest,
        modes=modes,
        bisimulation=args.bisimulation,
    )
    paths = write_reports(result, args.out, modes=modes)
    for mode in modes:
        counts = result.row(mode, "all", "ALL")
        print(
            f"{mode:>9}: P={counts.precision:.3f} R={counts.recall:.3f} "
            f"F1={counts.f1:.3f} (TP={counts.tp}, FP={counts.fp}, FN={counts.fn})"
        )
    print(f"pilot written to {paths['pilot']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "demo":
        args = _build_demo_parser().parse_args(argv[1:])
        return run_demo(Path(args.dataset) if args.dataset else None, Path(args.out))
    if argv and argv[0] == "generate":
        args = _build_generate_parser().parse_args(argv[1:])
        return run_generate(args)
    if argv and argv[0] == "evaluate":
        args = _build_evaluate_parser().parse_args(argv[1:])
        return run_evaluate(args)

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result, behavior_changed = _run(args)
    except ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _emit(result, args)
    if args.fail_on_change and behavior_changed:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
