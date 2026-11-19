"""Pandas/Matplotlib figures for the evaluation pilot.

This module is an optional analysis layer: the comparison engine, generator and
evaluation harness stay standard-library only.  The figures read the CSV files
written by ``bpmndiff evaluate`` and never re-run the diff.

Install the plotting dependency group once::

    pip install -e '.[viz]'
    python3 -m bpmndiff visualize
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median as _median

try:  # pragma: no cover - exercised through the CLI skip test
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:  # pragma: no cover - depends on the environment
    raise ImportError(
        "visualization requires pandas and matplotlib; "
        "install them with `pip install -e '.[viz]'`"
    ) from exc

from .evaluation import CHANGE_TYPES

MODE_ORDER = ("id", "name", "structure", "hybrid")
MODE_COLORS = {
    "id": "#0072B2",
    "name": "#D55E00",
    "structure": "#009E73",
    "hybrid": "#6A3D9A",
}
METRIC_COLORS = {
    "precision": "#0072B2",
    "recall": "#D55E00",
    "f1": "#009E73",
}
TEXT_COLOR = "#1F2933"
MUTED_COLOR = "#52606D"
GRID_COLOR = "#E4E7EB"

PILOT_COLUMNS = {
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
}
PAIR_COLUMNS = {
    "base_id",
    "variant",
    "alignment_mode",
    "scenario",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "predicted",
    "expected",
}


class VisualizationError(RuntimeError):
    """Raised when the evaluation CSVs are missing or malformed."""


@dataclass(frozen=True)
class FigureSet:
    files: dict[str, Path]


def _ordered_modes(values: object) -> list[str]:
    present = [str(value) for value in values]
    ordered = [mode for mode in MODE_ORDER if mode in present]
    ordered.extend(sorted(set(present) - set(ordered)))
    return ordered


def _style(plt_module) -> None:
    plt_module.rcParams.update(
        {
            "font.size": 10,
            "font.family": "DejaVu Sans",
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 10,
            "axes.edgecolor": "#CBD2D9",
            "axes.labelcolor": TEXT_COLOR,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": MUTED_COLOR,
            "ytick.color": MUTED_COLOR,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def _read_csv(path: Path, required: set[str]) -> pd.DataFrame:
    if not path.is_file():
        raise VisualizationError(f"missing evaluation file: {path}")
    frame = pd.read_csv(path)
    missing = required - set(frame.columns)
    if missing:
        raise VisualizationError(
            f"{path} is missing column(s): {', '.join(sorted(missing))}"
        )
    for column in ("tp", "fp", "fn", "support", "precision", "recall", "f1"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "predicted" in frame.columns:
        frame["predicted"] = pd.to_numeric(frame["predicted"], errors="coerce")
    return frame


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _subtitle(ax, text: str) -> None:
    title = ax.get_title(loc="left")
    if title:
        # Re-apply with padding so the subtitle has its own line above the axes.
        ax.set_title(title, loc="left", pad=26)
    ax.text(
        0.0,
        1.015,
        text,
        transform=ax.transAxes,
        fontsize=9,
        color=MUTED_COLOR,
        ha="left",
        va="bottom",
    )


def _grid(ax, axis: str = "y") -> None:
    ax.grid(axis=axis, color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)


def _annotate_heatmap(ax, values, rows: list[str], columns: list[str]) -> None:
    for row_index in range(len(rows)):
        for column_index in range(len(columns)):
            value = values[row_index][column_index]
            label = "—" if pd.isna(value) else f"{value:.2f}"
            ax.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color="white" if not pd.isna(value) and value > 0.55 else TEXT_COLOR,
            )


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_overall(pilot: pd.DataFrame, path: Path) -> None:
    overall = pilot[
        (pilot["scenario"] == "all") & (pilot["change_type"] == "ALL")
    ].set_index("alignment_mode")
    modes = _ordered_modes(overall.index)
    overall = overall.loc[modes]

    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    positions = list(range(len(modes)))
    width = 0.24
    for index, (column, label) in enumerate(
        (("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"))
    ):
        offset = (index - 1) * width
        bars = ax.bar(
            [position + offset for position in positions],
            overall[column].to_numpy(),
            width=width,
            label=label,
            color=METRIC_COLORS[column],
            edgecolor="white",
            linewidth=0.6,
        )
        ax.bar_label(bars, fmt="%.3f", fontsize=7.5, padding=2, color=MUTED_COLOR)

    ax.set_xticks(positions, modes)
    ax.set_ylim(0, 1.14)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Score")
    ax.set_title("Overall metrics by alignment mode")
    _subtitle(ax, "All 30 pairs · IDs kept and IDs regenerated")
    _grid(ax)
    ax.legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    _save(fig, path)


def plot_type_heatmap(pilot: pd.DataFrame, path: Path) -> None:
    subset = pilot[
        (pilot["scenario"] == "all") & (pilot["change_type"] != "ALL")
    ].copy()
    if subset.empty:
        raise VisualizationError("pilot.csv has no per-change-type rows")

    matrix = subset.pivot_table(
        index="change_type",
        columns="alignment_mode",
        values="f1",
        aggfunc="first",
    )
    support = subset.groupby("change_type")["support"].max()
    # Keep only types that exist in the ground truth. Types seen only as false
    # positives (support 0) are covered by the error analysis instead.
    rows = [
        change
        for change in CHANGE_TYPES
        if change in matrix.index and support.get(change, 0) > 0
    ]
    rows.extend(
        sorted(
            change
            for change in set(matrix.index) - set(rows)
            if support.get(change, 0) > 0
        )
    )
    modes = _ordered_modes(matrix.columns)
    matrix = matrix.reindex(index=rows, columns=modes)

    fig_height = 0.34 * len(rows) + 2.1
    fig, ax = plt.subplots(figsize=(8.4, fig_height))
    values = matrix.to_numpy(dtype=float)
    image = ax.imshow(values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    image.cmap = image.cmap.with_extremes(bad="#F0F2F5")
    ax.set_xticks(range(len(modes)), modes)
    ax.set_yticks(
        range(len(rows)),
        [f"{change} (n={int(support[change])})" for change in rows],
    )
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _annotate_heatmap(ax, values, rows, modes)
    ax.set_title("F1 by change type and alignment mode")
    _subtitle(ax, "Cell value: F1 · row label: ground-truth support")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02)
    colorbar.set_label("F1")
    colorbar.outline.set_visible(False)
    _save(fig, path)


def plot_id_churn(pilot: pd.DataFrame, path: Path) -> None:
    subset = pilot[
        (pilot["change_type"] == "ALL")
        & pilot["scenario"].isin(["keep_ids", "new_ids"])
    ]
    if subset["scenario"].nunique() < 2:
        raise VisualizationError("pilot.csv has no keep/new-ID scenario rows")

    matrix = subset.pivot_table(
        index="alignment_mode", columns="scenario", values="f1", aggfunc="first"
    )
    modes = _ordered_modes(matrix.index)
    matrix = matrix.loc[modes]

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    placed: dict[int, list[float]] = {0: [], 1: []}
    for index, mode in enumerate(modes):
        keep = float(matrix.loc[mode, "keep_ids"])
        churn = float(matrix.loc[mode, "new_ids"])
        color = MODE_COLORS.get(mode, "#3E4C59")
        ax.plot([0, 1], [keep, churn], color=color, linewidth=2.2, marker="o", markersize=7)
        for x_position, value in ((0, keep), (1, churn)):
            if any(abs(value - other) < 0.002 for other in placed[x_position]):
                continue
            placed[x_position].append(value)
            ax.annotate(
                f"{value:.3f}",
                (x_position, value),
                xytext=(8 if x_position else -8, 0),
                textcoords="offset points",
                ha="left" if x_position else "right",
                va="center",
                fontsize=8.5,
                color=color,
            )

    ax.set_xlim(-0.28, 1.28)
    ax.set_ylim(-0.04, 1.06)
    ax.set_xticks([0, 1], ["IDs kept", "IDs regenerated"])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("F1")
    ax.set_title("Effect of full ID regeneration")
    _subtitle(ax, "Same mutations, every XML ID rewritten")
    _grid(ax)
    ax.legend(
        handles=[
            plt.Line2D([], [], color=MODE_COLORS.get(mode, "#3E4C59"), linewidth=2.2, label=mode)
            for mode in modes
        ],
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
    )
    _save(fig, path)


def plot_pair_heatmap(pairs: pd.DataFrame, path: Path) -> None:
    if pairs.empty:
        raise VisualizationError("pilot_pairs.csv is empty")

    labels = [
        f"{base_id} · {variant}"
        for base_id, variant in dict.fromkeys(
            zip(pairs["base_id"].astype(str), pairs["variant"].astype(str))
        )
    ]
    pairs = pairs.copy()
    pairs["pair"] = pairs["base_id"].astype(str) + " · " + pairs["variant"].astype(str)
    matrix = pairs.pivot_table(
        index="pair", columns="alignment_mode", values="f1", aggfunc="first"
    )
    modes = _ordered_modes(matrix.columns)
    matrix = matrix.reindex(index=labels, columns=modes)

    fig, ax = plt.subplots(figsize=(7.6, 0.27 * len(labels) + 2.1))
    values = matrix.to_numpy(dtype=float)
    image = ax.imshow(values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    image.cmap = image.cmap.with_extremes(bad="#F0F2F5")
    ax.set_xticks(range(len(modes)), modes)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(length=0, labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    _annotate_heatmap(ax, values, labels, modes)

    base_ids = [label.split(" · ")[0] for label in labels]
    for index in range(1, len(base_ids)):
        if base_ids[index] != base_ids[index - 1]:
            ax.axhline(index - 0.5, color="white", linewidth=2.4)

    ax.set_title("Pair-level F1 by alignment mode")
    _subtitle(ax, "30 generated pairs, grouped by base diagram")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02)
    colorbar.set_label("F1")
    colorbar.outline.set_visible(False)
    _save(fig, path)


def plot_pair_distribution(pairs: pd.DataFrame, path: Path) -> None:
    modes = _ordered_modes(pairs["alignment_mode"].unique())
    data = [
        pairs.loc[pairs["alignment_mode"] == mode, "f1"].dropna().tolist()
        for mode in modes
    ]
    if not any(data):
        raise VisualizationError("pilot_pairs.csv has no F1 values")

    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    box = ax.boxplot(
        data,
        positions=range(1, len(modes) + 1),
        widths=0.5,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": TEXT_COLOR, "linewidth": 1.6},
        whiskerprops={"color": "#9AA5B1"},
        capprops={"color": "#9AA5B1"},
    )
    for patch, mode in zip(box["boxes"], modes):
        patch.set_facecolor(MODE_COLORS.get(mode, "#3E4C59"))
        patch.set_alpha(0.22)
        patch.set_edgecolor(MODE_COLORS.get(mode, "#3E4C59"))
        patch.set_linewidth(1.2)

    for index, values in enumerate(data, start=1):
        jitter = [((position % 7) - 3) * 0.045 for position in range(len(values))]
        ax.scatter(
            [index + offset for offset in jitter],
            values,
            s=18,
            color=MODE_COLORS.get(modes[index - 1], "#3E4C59"),
            alpha=0.8,
            linewidths=0,
            zorder=3,
        )
        if values:
            ax.annotate(
                f"median {_median(values):.3f}",
                (index, max(values)),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=8.5,
                color=MUTED_COLOR,
            )

    ax.set_xticks(range(1, len(modes) + 1), modes)
    ax.set_ylim(-0.05, 1.15)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("F1 per pair")
    ax.set_title("Distribution of pair-level F1")
    _subtitle(
        ax,
        f"{len(data[0]) if data else 0} pairs per mode · individual pairs overlaid",
    )
    _grid(ax)
    _save(fig, path)


def _correlation_axes(ax, matrix: pd.DataFrame) -> None:
    values = matrix.to_numpy(dtype=float)
    image = ax.imshow(values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")
    image.cmap = image.cmap.with_extremes(bad="#F0F2F5")
    labels = list(matrix.index)
    ax.set_xticks(range(len(labels)), labels, rotation=0)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row in range(len(labels)):
        for column in range(len(labels)):
            value = values[row][column]
            label = "n/a" if pd.isna(value) else f"{value:.2f}"
            ax.text(
                column,
                row,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color="white" if not pd.isna(value) and abs(value) > 0.6 else TEXT_COLOR,
            )
    return image


def _correlations(
    pairs: pd.DataFrame, value_column: str, modes: list[str]
) -> pd.DataFrame:
    pivoted = pairs.pivot_table(
        index=["base_id", "variant"],
        columns="alignment_mode",
        values=value_column,
        aggfunc="first",
    )
    pivoted = pivoted.reindex(columns=[mode for mode in modes if mode in pivoted.columns])
    # Drop modes with no variance: a constant series has no defined correlation.
    varying = [
        mode
        for mode in pivoted.columns
        if pivoted[mode].dropna().nunique() > 1
    ]
    return pivoted[varying].corr()


def plot_correlation(pairs: pd.DataFrame, path: Path, csv_path: Path) -> None:
    modes = _ordered_modes(pairs["alignment_mode"].unique())
    f1_correlation = _correlations(pairs, "f1", modes)
    count_correlation = _correlations(pairs, "predicted", modes)
    if f1_correlation.empty and count_correlation.empty:
        raise VisualizationError("not enough variance for a correlation matrix")

    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.7))
    fig.subplots_adjust(top=0.77, bottom=0.09, left=0.08, right=0.90, wspace=0.42)
    panels = (
        (axes[0], f1_correlation, "Per-pair F1"),
        (axes[1], count_correlation, "Predicted operation count"),
    )
    image = None
    for ax, matrix, title in panels:
        if matrix.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, "n/a", ha="center", va="center", color=MUTED_COLOR)
            continue
        image = _correlation_axes(ax, matrix)
    # Titles are placed in figure coordinates so both panels line up even when
    # the square matrices have different sizes (3x3 vs 4x4).
    top = max(ax.get_position().y1 for ax in axes)
    for ax, _, title in panels:
        fig.text(
            ax.get_position().x0,
            top + 0.02,
            title,
            fontsize=11,
            fontweight="bold",
            color=TEXT_COLOR,
            ha="left",
            va="bottom",
        )
    fig.suptitle(
        "Correlation between alignment modes",
        x=0.02,
        y=0.975,
        ha="left",
        fontsize=12,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    fig.text(
        0.02,
        0.91,
        "Pearson r over the 30 pairs · hybrid F1 is constant (1.000), so it is "
        "excluded from the left panel",
        fontsize=8.5,
        color=MUTED_COLOR,
        ha="left",
    )
    if image is not None:
        colorbar = fig.colorbar(image, ax=list(axes), fraction=0.025, pad=0.03)
        colorbar.set_label("Pearson r")
        colorbar.outline.set_visible(False)
    _save(fig, path)

    rows = []
    for metric, matrix in (
        ("pair_f1", f1_correlation),
        ("predicted_operations", count_correlation),
    ):
        for row_label in matrix.index:
            for column_label in matrix.columns:
                rows.append(
                    {
                        "metric": metric,
                        "mode_a": row_label,
                        "mode_b": column_label,
                        "pearson_r": matrix.loc[row_label, column_label],
                    }
                )
    pd.DataFrame(rows).to_csv(csv_path, index=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def build_figures(
    results_dir: str | Path, out_dir: str | Path
) -> FigureSet:
    """Read ``pilot.csv``/``pilot_pairs.csv`` and write PNG figures."""
    results = Path(results_dir)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    _style(plt)

    pilot = _read_csv(results / "pilot.csv", PILOT_COLUMNS)
    pairs = _read_csv(results / "pilot_pairs.csv", PAIR_COLUMNS)

    files = {
        "overall": output / "mode_overall.png",
        "type_heatmap": output / "type_mode_heatmap.png",
        "id_churn": output / "id_churn.png",
        "pair_heatmap": output / "pair_mode_heatmap.png",
        "distribution": output / "pair_f1_distribution.png",
        "correlation": output / "mode_correlation.png",
        "correlation_csv": output / "mode_correlation.csv",
    }

    plot_overall(pilot, files["overall"])
    plot_type_heatmap(pilot, files["type_heatmap"])
    plot_id_churn(pilot, files["id_churn"])
    plot_pair_heatmap(pairs, files["pair_heatmap"])
    plot_pair_distribution(pairs, files["distribution"])
    plot_correlation(pairs, files["correlation"], files["correlation_csv"])
    return FigureSet(files=files)
