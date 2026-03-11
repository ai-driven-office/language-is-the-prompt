#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "results" / "summary.json"
FIGURES_DIR = REPO_ROOT / "figures"


def load_summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def ensure_figures_dir() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def svg_text(x: int, y: int, text: str, size: int = 16, weight: str = "normal", fill: str = "#1f2937") -> str:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Inter,Arial,sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{safe}</text>'
    )


def render_main_chart(summary: dict) -> None:
    languages = summary["main_benchmark"]["languages"]
    rows = sorted(
        (
            {
                "language": language,
                "pass_rate": values["pass_rate"],
                "passed": values["passed"],
                "total": values["total"],
            }
            for language, values in languages.items()
        ),
        key=lambda row: (-row["pass_rate"], row["language"]),
    )

    width = 1280
    row_height = 34
    chart_left = 230
    chart_width = 820
    top = 100
    height = top + len(rows) * row_height + 80
    max_rate = max(row["pass_rate"] for row in rows)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        svg_text(40, 48, "GPT-5.4 Medium on ACB-Full", size=30, weight="700"),
        svg_text(
            40,
            76,
            f'Corrected local run on 3,920 problems across 20 languages. Overall: {summary["main_benchmark"]["pass_rate"]:.1f}% pass@1.',
            size=16,
            fill="#475569",
        ),
    ]

    for tick in range(0, 101, 20):
        x = chart_left + chart_width * tick / 100
        parts.append(f'<line x1="{x}" y1="{top - 10}" x2="{x}" y2="{height - 40}" stroke="#e2e8f0" stroke-width="1"/>')
        parts.append(svg_text(int(x - 10), top - 18, f"{tick}%", size=12, fill="#64748b"))

    for index, row in enumerate(rows):
        y = top + index * row_height
        bar_width = chart_width * row["pass_rate"] / max_rate
        fill = "#0f766e" if row["pass_rate"] >= 60 else "#2563eb" if row["pass_rate"] >= 50 else "#d97706"
        parts.append(svg_text(40, y + 20, row["language"], size=15, weight="600"))
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{chart_width}" height="20" rx="10" fill="#e2e8f0"/>')
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{bar_width:.1f}" height="20" rx="10" fill="{fill}"/>')
        parts.append(
            svg_text(
                chart_left + chart_width + 18,
                y + 16,
                f'{row["passed"]}/{row["total"]}  ({row["pass_rate"]:.1f}%)',
                size=13,
                fill="#334155",
            )
        )

    parts.append("</svg>")
    (FIGURES_DIR / "fork_acb_full_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def render_extension_chart(summary: dict) -> None:
    rows = [
        {
            "language": "typescript_effect",
            "pass_rate": summary["extension_slices"]["typescript_effect"]["pass_rate"],
            "validated": None,
            "source_rows": summary["extension_slices"]["typescript_effect"]["source_rows"],
            "passed": summary["extension_slices"]["typescript_effect"]["passed"],
            "label": "legacy extension run",
        },
        {
            "language": "gleam",
            "pass_rate": summary["extension_slices"]["gleam"]["pass_rate_on_validated_rows"],
            "validated": summary["extension_slices"]["gleam"]["validated_rows"],
            "source_rows": summary["extension_slices"]["gleam"]["source_rows"],
            "passed": summary["extension_slices"]["gleam"]["passed"],
            "label": f'validated {summary["extension_slices"]["gleam"]["validated_rows"]}/{summary["extension_slices"]["gleam"]["source_rows"]}',
        },
        {
            "language": "lean4",
            "pass_rate": summary["extension_slices"]["lean4"]["pass_rate_on_validated_rows"],
            "validated": summary["extension_slices"]["lean4"]["validated_rows"],
            "source_rows": summary["extension_slices"]["lean4"]["source_rows"],
            "passed": summary["extension_slices"]["lean4"]["passed"],
            "label": f'validated {summary["extension_slices"]["lean4"]["validated_rows"]}/{summary["extension_slices"]["lean4"]["source_rows"]}',
        },
    ]

    width = 1120
    height = 520
    chart_left = 180
    chart_width = 760
    top = 120
    row_gap = 105

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        svg_text(40, 48, "Extension Language Slices", size=30, weight="700"),
        svg_text(
            40,
            76,
            "Fork-only translated benchmark slices. Gleam and Lean4 are reported on canonical-validated translated subsets.",
            size=16,
            fill="#475569",
        ),
    ]

    for tick in range(0, 61, 10):
        x = chart_left + chart_width * tick / 60
        parts.append(f'<line x1="{x}" y1="{top - 10}" x2="{x}" y2="{height - 40}" stroke="#e2e8f0" stroke-width="1"/>')
        parts.append(svg_text(int(x - 10), top - 18, f"{tick}%", size=12, fill="#64748b"))

    colors = {
        "typescript_effect": "#7c3aed",
        "gleam": "#0f766e",
        "lean4": "#2563eb",
    }
    for index, row in enumerate(rows):
        y = top + index * row_gap
        bar_width = chart_width * row["pass_rate"] / 60
        parts.append(svg_text(40, y + 18, row["language"], size=18, weight="700"))
        parts.append(svg_text(40, y + 42, row["label"], size=13, fill="#64748b"))
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{chart_width}" height="28" rx="14" fill="#e2e8f0"/>')
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{bar_width:.1f}" height="28" rx="14" fill="{colors[row["language"]]}"/>')
        parts.append(svg_text(chart_left + chart_width + 20, y + 20, f'{row["passed"]}/{row["validated"] or row["source_rows"]}  ({row["pass_rate"]:.1f}%)', size=14))

    parts.append("</svg>")
    (FIGURES_DIR / "fork_extension_languages_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    ensure_figures_dir()
    summary = load_summary()
    render_main_chart(summary)
    render_extension_chart(summary)
    print("Wrote figures/fork_acb_full_gpt_5_4_medium.svg")
    print("Wrote figures/fork_extension_languages_gpt_5_4_medium.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
