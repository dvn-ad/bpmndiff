"""Human-readable and machine-readable report rendering."""

from __future__ import annotations

import json
import os
from typing import Iterable

def _short(path: str) -> str:
    if not path:
        return ""
    return os.path.basename(path)


def _trace(trace: Iterable[str]) -> str:
    return " -> ".join(trace) if trace else "(empty trace)"


def _behavior_word(equivalent: bool | None) -> str:
    if equivalent is True:
        return "EQUIVALENT"
    if equivalent is False:
        return "NOT EQUIVALENT"
    return "INCONCLUSIVE"


def _yes_no(value) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _op_target(operation: dict) -> str:
    payload = operation.get("before") or operation.get("after") or {}
    if operation["element"] == "flow":
        if payload.get("source") or payload.get("target"):
            return f'{payload.get("source", "?")} -> {payload.get("target", "?")}'
        return "sequence flow"
    return payload.get("name", "?")


def _format_operation(operation: dict) -> str:
    op = operation["op"]
    detail = operation.get("detail", "")
    target = _op_target(operation)
    review = "  [needs review]" if operation.get("needs_review") else ""
    if op in {"RENAME_NODE", "RENAME"}:
        before = (operation.get("before") or {}).get("name", "?")
        after = (operation.get("after") or {}).get("name", "?")
        subtype = f" ({operation['subtype']})" if "subtype" in operation else ""
        return f'{op:<20} "{before}" -> "{after}"{subtype}{review}'
    if op in {"RENAME_LANE", "RENAME_SWIMLANE"}:
        before = (operation.get("before") or {}).get("name", "?")
        after = (operation.get("after") or {}).get("name", "?")
        return f'{op:<20} "{before}" -> "{after}"{review}'
    if op in {"MOVE_LANE", "CHANGE_SWIMLANE"}:
        before = operation.get("before") or {}
        after = operation.get("after") or {}
        before_lane = before.get("lane") or "(unassigned)"
        after_lane = after.get("lane") or "(unassigned)"
        return (
            f'{op:<20} {before.get("name", "?")}: '
            f'"{before_lane}" -> "{after_lane}"{review}'
        )
    if detail:
        return f"{op:<20} {detail}{review}"
    return f"{op:<20} {target}{review}"


def _render_a_text(result: dict) -> str:
    ref = result["reference"]
    var = result["variant"]
    alignment = result["alignment"]
    counts = alignment["counts"]
    behavior = result["behavior"]
    fusion = result["fusion"]
    lines: list[str] = []
    line = "=" * 78
    lines.append(line)
    lines.append(" bpmndiff | Mode A | pairwise process comparison")
    lines.append(line)
    lines.append(f" Reference : {ref['name']}  ({ref['format']}, {_short(ref['source'])})")
    lines.append(f"             {ref['stats']['nodes']} nodes, {ref['stats']['edges']} flows")
    lines.append(f" Variant   : {var['name']}  ({var['format']}, {_short(var['source'])})")
    lines.append(f"             {var['stats']['nodes']} nodes, {var['stats']['edges']} flows")
    lines.append("")
    lines.append(
        " Alignment : "
        + ", ".join(
            [
                f"{counts.get('identical', 0)} identical",
                f"{counts.get('synonym', 0)} synonym",
                f"{counts.get('meaning_changed', 0)} meaning-changed",
                f"{len([p for p in alignment['pairs'] if p['a'] and not p['b']])} deleted",
                f"{len([p for p in alignment['pairs'] if p['b'] and not p['a']])} inserted",
            ]
        )
    )
    if counts.get("needs_review"):
        lines.append(f"             {counts['needs_review']} pair(s) flagged needs-review")
    lines.append("")
    lines.append(f" Edit script ({len(result['operations'])} operations)")
    lines.append("-" * 78)
    if result["operations"]:
        current_cat = None
        for operation in result["operations"]:
            cat = operation.get("category")
            cat_name = operation.get("category_name")
            if cat and cat != current_cat:
                current_cat = cat
                lines.append(f"  [{cat}. {cat_name}]")
            lines.append("    " + _format_operation(operation))
    else:
        lines.append("  (no differences)")
    lines.append("")
    lines.append(" Behaviour")
    lines.append("-" * 78)
    lines.append(f"  Trace equivalence      : {_behavior_word(behavior.get('equivalent'))}")
    lines.append(f"  Method                 : {behavior.get('method', 'n/a')}")
    if behavior.get("truncated"):
        lines.append("  Note                   : state exploration was truncated (see --max-states)")
    counterexample = behavior.get("counterexample")
    if counterexample:
        lines.append(
            f"  Counterexample [{counterexample['direction']}] : {_trace(counterexample['trace'])}"
        )
        lines.append(f"     {counterexample['detail']}")
    bisim = behavior.get("branching_bisimulation")
    if bisim:
        lines.append(
            f"  Branching bisimulation : {_behavior_word(bisim.get('equivalent'))}"
            f" ({bisim.get('reason', '')})"
        )
    samples = behavior.get("trace_samples", {})
    ref_samples = (samples.get("reference") or {}).get("traces", [])
    if ref_samples:
        lines.append("  Reference trace sample :")
        for trace in ref_samples[:3]:
            lines.append("     " + _trace(trace))
    lines.append("")
    fragments = result["fragments"]
    lines.append(f" SESE fragments: {fragments['count']} region(s), {len(fragments['affected'])} affected")
    lines.append("-" * 78)
    if fragments["affected"]:
        for fragment in fragments["affected"]:
            status = fragment.get("status")
            if status == "checked":
                state = _behavior_word(fragment.get("equivalent"))
                lines.append(f"  {fragment['id']} [{fragment['size']} nodes] {state}")
                if fragment.get("counterexample"):
                    ce = fragment["counterexample"]
                    lines.append(f"      counterexample [{ce['direction']}]: {_trace(ce['trace'])}")
            else:
                lines.append(
                    f"  {fragment['id']} [{fragment['size']} nodes] SKIPPED - {fragment.get('reason', '')}"
                )
    else:
        lines.append("  (no affected region)")
    lines.append("")
    lines.append(" Fusion verdict")
    lines.append("-" * 78)
    lines.append(f"  Overall     : {fusion['overall']}")
    lines.append(f"  Element mix : {fusion['verdict_counts']}")
    if fusion.get("needs_review"):
        lines.append("  Review      : one or more element pairs need manual/LLM review")
    return "\n".join(lines)


def render_text(result: dict) -> str:
    return _render_a_text(result)


def render_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def _render_a_markdown(result: dict) -> str:
    ref, var = result["reference"], result["variant"]
    alignment = result.get("alignment", {})
    counts = alignment.get("counts", {})
    behavior, fusion = result["behavior"], result["fusion"]
    lines = [
        f"# Pairwise comparison: {ref['name']} vs {var['name']}",
        "",
        _md_table(
            ["Model", "Format", "Nodes", "Flows", "Source"],
            [
                ["Reference", ref["format"], ref["stats"]["nodes"], ref["stats"]["edges"], ref["source"]],
                ["Variant", var["format"], var["stats"]["nodes"], var["stats"]["edges"], var["source"]],
            ],
        ),
        "",
        "## Alignment Summary",
        "",
        _md_table(
            ["Identical", "Synonym", "Meaning Changed", "Deleted", "Inserted", "Needs Review"],
            [
                [
                    str(counts.get("identical", 0)),
                    str(counts.get("synonym", 0)),
                    str(counts.get("meaning_changed", 0)),
                    str(len([p for p in alignment.get("pairs", []) if p.get("a") and not p.get("b")])),
                    str(len([p for p in alignment.get("pairs", []) if p.get("b") and not p.get("a")])),
                    str(counts.get("needs_review", 0)),
                ]
            ],
        ),
        "",
        f"## Edit script ({len(result['operations'])} operations)",
        "",
    ]
    if result["operations"]:
        rows = [
            [
                f"{op.get('category', '-')}. {op.get('category_name', '')}" if op.get("category") else "-",
                op["op"],
                _op_target(op),
                op.get("detail", ""),
                "yes" if op.get("needs_review") else "no",
            ]
            for op in result["operations"]
        ]
        lines.append(_md_table(["Category", "Operation", "Element", "Detail", "Review"], rows))
    else:
        lines.append("_No differences._")

    lines += ["", "## Behavioural verification", ""]
    lines.append(f"- Trace equivalence: **{_behavior_word(behavior.get('equivalent'))}**")
    lines.append(f"- Method: `{behavior.get('method', 'n/a')}`")
    if behavior.get("counterexample"):
        ce = behavior["counterexample"]
        lines.append(f"- Counterexample ({ce['direction']}): `{_trace(ce['trace'])}`")
        lines.append(f"  - {ce['detail']}")
    bisim = behavior.get("branching_bisimulation")
    if bisim:
        lines.append(f"- Branching bisimulation: **{_behavior_word(bisim.get('equivalent'))}**")

    if behavior.get("traces_a"):
        lines += ["", "### Reference trace sample", ""]
        for tr in behavior["traces_a"][:3]:
            lines.append(f"- `{_trace(tr)}`")

    lines += ["", f"## SESE fragments ({result['fragments']['count']} regions)", ""]
    if result["fragments"]["affected"]:
        rows = []
        for fragment in result["fragments"]["affected"]:
            state = _behavior_word(fragment.get("equivalent")) if fragment.get("status") == "checked" else "skipped"
            counterexample = fragment.get("counterexample") or {}
            rows.append([fragment["id"], fragment["size"], state, _trace(counterexample.get("trace", []))])
        lines.append(_md_table(["Region", "Nodes", "Behaviour", "Counterexample"], rows))
    else:
        lines.append("_No affected region._")

    lines += [
        "",
        "## Fusion verdict",
        "",
        f"**{fusion['overall']}**",
        "",
        f"- Element verdicts: `{fusion['verdict_counts']}`",
        f"- Operations: `{fusion['operation_counts']}`",
        f"- Needs review: {fusion['needs_review']}",
    ]
    return "\n".join(lines)


def render_markdown(result: dict) -> str:
    return _render_a_markdown(result)
