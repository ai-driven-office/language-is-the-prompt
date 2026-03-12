#!/usr/bin/env python3
"""Rebuild editable figure PDFs for the Elixir arXiv paper.

This script reconstructs the paper figures from CSV data extracted from the
surviving LaTeX source and the values shown in the figures/tables.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "figures"

COLORS: Dict[str, str] = {
    "elixir": "#5B4B8A",
    "python": "#C97A00",
    "typescript": "#2A9D8F",
    "neutral": "#B7BDC6",
    "dark": "#3B4754",
    "kotlin": "#4C78A8",
    "csharp": "#2A9D8F",
    "javascript": "#C44E52",
    "examples": "#E1C44F",
    "contracts": "#5CB8A5",
    "grid": "#D1D5DB",
    "text": "#111827",
    "bg": "#F5F5F4",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 200,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": COLORS["bg"],
        "figure.facecolor": "white",
    }
)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="pdf")
    plt.close(fig)


def fig_leaderboard() -> None:
    rows = read_csv(DATA / "leaderboard.csv")
    rows.sort(key=lambda r: float(r["pass1"]), reverse=True)

    languages = [r["language"] for r in rows]
    pass1 = [float(r["pass1"]) for r in rows]
    hard = [float(r["hard_pct"]) for r in rows]
    y = list(range(len(rows)))

    bar_colors = []
    for lang in languages:
        if lang == "Elixir":
            bar_colors.append(COLORS["elixir"])
        elif lang == "Python":
            bar_colors.append(COLORS["python"])
        elif lang == "TypeScript":
            bar_colors.append(COLORS["typescript"])
        else:
            bar_colors.append(COLORS["neutral"])

    fig, ax = plt.subplots(figsize=(8.8, 7.4))
    ax2 = ax.twiny()

    ax.barh(y, pass1, color=bar_colors, edgecolor="none", height=0.8)
    ax2.scatter(hard, y, s=22, color=COLORS["dark"], alpha=0.85, zorder=5)

    for yi, val in zip(y, pass1):
        ax.text(val + 0.8, yi, f"{val:.1f}", va="center", ha="left", fontsize=10, color=COLORS["text"])

    ax.set_yticks(y)
    ax.set_yticklabels(languages)
    ax.invert_yaxis()
    ax.set_xlim(0, 92)
    ax2.set_xlim(0, 80)
    ax.set_xlabel("Pass@1 (%)")
    ax2.set_xlabel("Hard-task share (%)")
    ax.set_title("AutoCodeBench leaderboard reproduced with GPT-5.4 (196 tasks/language)")

    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8, alpha=0.7)
    ax2.grid(False)

    legend_items = [
        Line2D([0], [0], color=COLORS["elixir"], lw=8, label="Elixir"),
        Line2D([0], [0], color=COLORS["python"], lw=8, label="Python"),
        Line2D([0], [0], color=COLORS["typescript"], lw=8, label="TypeScript"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["dark"], markersize=7, label="Hard-task share"),
    ]
    ax.legend(handles=legend_items, frameon=False, loc="lower right")
    fig.tight_layout()
    save(fig, "figure_1_leaderboard.pdf")


def fig_design_space() -> None:
    rows = read_csv(DATA / "leaderboard.csv")

    x = [float(r["cf_score"]) for r in rows]
    y = [-float(r["mutability"]) for r in rows]
    docs = [float(r["docs"]) for r in rows]
    pass1 = [float(r["pass1"]) for r in rows]
    langs = [r["language"] for r in rows]
    sizes = [d * 24 for d in docs]

    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    sc = ax.scatter(x, y, s=sizes, c=pass1, cmap="viridis", alpha=0.9, edgecolors="none")
    ax.set_title("Language design-space map: Elixir is the only far-upper-right outlier")
    ax.set_xlabel("Control-flow explicitness score (higher is better)")
    ax.set_ylabel("State clarity = - mutability burden (higher is better)")
    ax.grid(color=COLORS["grid"], linewidth=0.8, alpha=0.7)

    annotate = {
        "Elixir": (0.08, 0.18),
        "Racket": (0.05, 0.18),
        "Python": (0.05, -0.10),
        "Kotlin": (0.07, 0.10),
        "TypeScript": (0.05, -0.18),
        "JavaScript": (0.05, -0.12),
        "C#": (0.05, 0.12),
        "Rust": (0.05, 0.14),
    }
    for lang, dxdy in annotate.items():
        idx = langs.index(lang)
        dx, dy = dxdy
        ax.text(x[idx] + dx, y[idx] + dy, lang, fontsize=10, color=COLORS["text"])

    ax.text(3.85, -29.9, "Bubble size = docs proxy", fontsize=10, color=COLORS["dark"])
    cbar = fig.colorbar(sc, ax=ax, shrink=0.88)
    cbar.set_label("Pass@1 (%)")
    fig.tight_layout()
    save(fig, "figure_2_design_space.pdf")


def fig_difficulty_resilience() -> None:
    rows = read_csv(DATA / "difficulty_buckets.csv")
    stages = ["Easy", "Medium", "Hard"]
    x = [0, 1, 2]

    style = {
        "Elixir": (COLORS["elixir"], "o"),
        "Kotlin": (COLORS["kotlin"], "^"),
        "C#": (COLORS["csharp"], "D"),
        "Python": (COLORS["python"], "s"),
        "JavaScript": (COLORS["javascript"], "v"),
    }

    fig, ax = plt.subplots(figsize=(7.8, 4.9))
    for row in rows:
        lang = row["language"]
        vals = [float(row["easy"]), float(row["medium"]), float(row["hard"])]
        color, marker = style[lang]
        ax.plot(x, vals, marker=marker, markersize=7, linewidth=2.2, color=color, label=lang)

    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylim(20, 103)
    ax.set_ylabel("Pass@1 (%)")
    ax.set_title("Difficulty resilience: Elixir barely degrades as tasks get harder")
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8, alpha=0.7)

    ax.annotate(
        "Elixir: -10.3 pp",
        xy=(2, 86.3),
        xytext=(1.2, 94.5),
        arrowprops=dict(arrowstyle="-", lw=1.2, color=COLORS["elixir"]),
        color=COLORS["elixir"],
        fontsize=11,
    )
    ax.annotate(
        "Python: -50.4 pp",
        xy=(2, 31.6),
        xytext=(1.1, 44.0),
        arrowprops=dict(arrowstyle="-", lw=1.2, color=COLORS["python"]),
        color=COLORS["python"],
        fontsize=11,
    )

    ax.legend(frameon=False, ncol=3, loc="lower left")
    fig.tight_layout()
    save(fig, "figure_3_difficulty_resilience.pdf")


def fig_suite_a() -> None:
    rows = read_csv(DATA / "suite_a.csv")
    labels = [r["label"] for r in rows]
    vals = [float(r["pass1"]) for r in rows]
    deltas = [float(r["delta"]) for r in rows]
    x = list(range(len(rows)))
    colors = [COLORS["elixir"], COLORS["elixir"], COLORS["neutral"], COLORS["neutral"]]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(x, vals, color=colors, edgecolor="none", width=0.7)
    ax.axhline(43.9, color=COLORS["python"], linestyle="--", linewidth=1.3, alpha=0.9)
    ax.text(2.65, 45.8, "Python baseline 43.9%\non ACB", color=COLORS["python"], fontsize=10, ha="left", va="bottom")

    for idx, (bar, val, delta) in enumerate(zip(bars, vals, deltas)):
        if idx == 0:
            text = f"{val:.1f}%"
        elif idx == 1:
            text = f"{val:.1f}%\n(no change)"
        else:
            text = f"{val:.1f}%\n({delta:+.1f} pp)"
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.2, text, ha="center", va="bottom", fontsize=10, color=COLORS["text"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 95)
    ax.set_ylabel("Pass@1 (%)")
    ax.set_title("Suite A: documentation structure is the dominant causal signal")
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8, alpha=0.7)
    fig.tight_layout()
    save(fig, "figure_4_suite_a_ablation.pdf")


def fig_factorial_effects() -> None:
    left_rows = read_csv(DATA / "factorial_main_effects.csv")
    right_rows = read_csv(DATA / "contract_effect_by_language.csv")

    # Reorder left panel to match the published figure's visual emphasis.
    order = ["state_guidance", "docs_rich", "examples", "contracts_explicit"]
    left_sorted = [next(r for r in left_rows if r["factor"] == name) for name in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.2), gridspec_kw={"width_ratios": [1.25, 0.95]})

    left_labels = [r["label"] for r in left_sorted]
    left_vals = [float(r["effect"]) for r in left_sorted]
    left_colors = [COLORS["contracts"] if r["factor"] == "contracts_explicit" else COLORS["neutral"] for r in left_sorted]
    y = list(range(len(left_sorted)))
    ax1.barh(y, left_vals, color=left_colors, edgecolor="none", height=0.62)
    ax1.axvline(0, color=COLORS["dark"], linewidth=1.0)
    ax1.set_yticks(y)
    ax1.set_yticklabels(left_labels)
    ax1.set_xlabel("Matched effect on pass scale")
    ax1.set_title("Portable gains come from explicit contracts, not generic extra prose\n\nMain effects in 384-row fractional-factorial study", fontsize=12)
    ax1.grid(axis="x", color=COLORS["grid"], linewidth=0.8, alpha=0.7)

    for yi, row in zip(y, left_sorted):
        val = float(row["effect"])
        sig = row["significant"] == "1"
        marker = " *" if sig else ""
        x_text = val + 0.012 if val >= 0 else val - 0.012
        ha = "left" if val >= 0 else "right"
        ax1.text(x_text, yi, f"{val:+.3f}{marker}", va="center", ha=ha, fontsize=10, color=COLORS["text"])

    right_labels = [r["language"] for r in right_rows]
    right_vals = [float(r["effect"]) for r in right_rows]
    right_colors = [COLORS["contracts"] if r["significant"] == "1" else COLORS["neutral"] for r in right_rows]
    x = list(range(len(right_rows)))
    bars = ax2.bar(x, right_vals, color=right_colors, edgecolor="none", width=0.62)
    ax2.set_xticks(x)
    ax2.set_xticklabels(right_labels)
    ax2.set_ylim(0, 0.55)
    ax2.set_ylabel("Contract-effect")
    ax2.set_title("By-language contract effect", fontsize=12)
    ax2.grid(axis="y", color=COLORS["grid"], linewidth=0.8, alpha=0.7)

    for bar, row in zip(bars, right_rows):
        val = float(row["effect"])
        sig = row["significant"] == "1"
        marker = " *" if sig else ""
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:+.3f}{marker}", ha="center", va="bottom", fontsize=10)

    fig.tight_layout()
    save(fig, "figure_5_factorial_effects.pdf")


def fig_docs_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.2, 2.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.95,
        "Elixir's documentation architecture is a single legibility stack",
        ha="center",
        va="top",
        fontsize=15,
        color=COLORS["text"],
    )

    boxes = [
        (0.03, 0.33, 0.20, 0.42, "#D8D4E1", "Source code\n@moduledoc, @doc,\n@spec"),
        (0.28, 0.33, 0.20, 0.42, "#CBD5E1", "Executable examples\nExUnit.DocTest\nkeeps docs fresh"),
        (0.53, 0.33, 0.20, 0.42, "#D0E7E4", "Standard generation\nExDoc produces\nuniform HTML/EPUB"),
        (0.78, 0.33, 0.20, 0.42, "#E9DFC8", "Ecosystem delivery\nHexDocs + runtime\nintrospection"),
    ]

    for x0, y0, w, h, color, text in boxes:
        patch = FancyBboxPatch(
            (x0, y0),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.018",
            linewidth=1.0,
            edgecolor="#C9B87A",
            facecolor=color,
        )
        ax.add_patch(patch)
        ax.text(x0 + w / 2, y0 + h / 2, text, ha="center", va="center", fontsize=11, color=COLORS["dark"])

    for x1, x2 in [(0.23, 0.28), (0.48, 0.53), (0.73, 0.78)]:
        arrow = FancyArrowPatch((x1, 0.54), (x2, 0.54), arrowstyle="-|>", mutation_scale=13, linewidth=1.4, color=COLORS["dark"])
        ax.add_patch(arrow)

    ax.text(
        0.5,
        0.13,
        "The key claim is architectural, not volumetric: purpose, contracts, examples, publication, and retrieval are co-located.",
        ha="center",
        va="center",
        fontsize=12,
        color=COLORS["dark"],
    )

    fig.tight_layout()
    save(fig, "figure_6_docs_pipeline.pdf")


def fig_robustness() -> None:
    rows = read_csv(DATA / "robustness.csv")
    labels = [r["label"] for r in rows]
    lows = [float(r["low"]) for r in rows]
    highs = [float(r["high"]) for r in rows]
    centers = [float(r["center"]) for r in rows]
    colors = [COLORS["contracts"] if r["group"] == "Contracts" else COLORS["examples"] for r in rows]
    y = list(range(len(rows)))[::-1]

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    for yi, low, high, center, color in zip(y, lows, highs, centers, colors):
        ax.plot([low, high], [yi, yi], color=color, linewidth=5, solid_capstyle="round")
        ax.scatter([center], [yi], color=COLORS["dark"], s=28, zorder=5)

    ax.axvline(0, color=COLORS["dark"], linewidth=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Effect range on pass scale")
    ax.set_title("Quick robustness checks: examples stay modest, contracts stay positive")
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8, alpha=0.7)
    ax.set_xlim(-0.10, 0.55)
    fig.tight_layout()
    save(fig, "figure_A1_robustness.pdf")


def main() -> None:
    fig_leaderboard()
    fig_design_space()
    fig_difficulty_resilience()
    fig_suite_a()
    fig_factorial_effects()
    fig_docs_pipeline()
    fig_robustness()
    print("[OK] wrote figure PDFs to", OUT)


if __name__ == "__main__":
    main()
