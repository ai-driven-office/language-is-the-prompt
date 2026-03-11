#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "results" / "summary.json"
FIGURES_DIR = REPO_ROOT / "figures"
RESULTS_DIR = REPO_ROOT / "results"


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


def svg_rect(x: int, y: int, width: int, height: int, fill: str, radius: int = 20, stroke: str | None = None, stroke_width: int = 1) -> str:
    stroke_attr = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}"{stroke_attr}/>'
    )


def write_yaml(path: Path, payload: dict) -> None:
    def dump(value: object, indent: int = 0) -> list[str]:
        prefix = "  " * indent
        if isinstance(value, dict):
            lines: list[str] = []
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(dump(item, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {scalar(item)}")
            return lines
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.extend(dump(item, indent + 1))
                else:
                    lines.append(f"{prefix}- {scalar(item)}")
            return lines
        return [f"{prefix}{scalar(value)}"]

    def scalar(value: object) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        if text == "" or any(ch in text for ch in [":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", ">", "%", "@", "`", "\"", "'"]) or text.strip() != text:
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return text

    path.write_text("\n".join(dump(payload)) + "\n", encoding="utf-8")


def export_yaml(summary: dict) -> None:
    write_yaml(RESULTS_DIR / "summary.yaml", summary)
    write_yaml(RESULTS_DIR / "main_benchmark.yaml", summary["main_benchmark"])
    write_yaml(RESULTS_DIR / "extension_slices.yaml", summary["extension_slices"])


def render_overview(summary: dict) -> None:
    width = 1280
    height = 720
    cards = [
        ("ACB-Full", "53.3%", "2088 / 3920", "20 original languages", "#0f766e"),
        ("Gleam", "20.5%", "25 / 122", "validated translated subset", "#d97706"),
        ("Lean4", "28.8%", "36 / 125", "validated translated subset", "#2563eb"),
        ("TS Effect", "53.6%", "105 / 196", "legacy extension slice", "#7c3aed"),
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#f8fafc"/>',
        '<stop offset="100%" stop-color="#eef2ff"/>',
        "</linearGradient>",
        "</defs>",
        '<rect width="100%" height="100%" fill="url(#bg)"/>',
        svg_text(56, 72, "AutoCodeBenchmark Fork Update", size=34, weight="700"),
        svg_text(56, 106, "GPT-5.4 Medium local benchmark results and extension-language slices", size=18, fill="#475569"),
        svg_text(56, 138, "Snapshot date: 2026-03-11", size=14, fill="#64748b"),
    ]

    for index, (title, pct, score, note, color) in enumerate(cards):
        col = index % 2
        row = index // 2
        x = 56 + col * 590
        y = 190 + row * 220
        parts.append(svg_rect(x, y, 550, 180, "#ffffff", radius=28, stroke="#dbe4f0"))
        parts.append(svg_rect(x + 22, y + 22, 12, 136, color, radius=6))
        parts.append(svg_text(x + 56, y + 54, title, size=22, weight="700"))
        parts.append(svg_text(x + 56, y + 104, pct, size=42, weight="700", fill=color))
        parts.append(svg_text(x + 56, y + 136, score, size=18, weight="600", fill="#334155"))
        parts.append(svg_text(x + 56, y + 164, note, size=14, fill="#64748b"))

    parts.append(svg_text(56, 654, "See RESULTS.md and reports/fork_update_gpt_5_4_medium.md for methodology and caveats.", size=15, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_results_overview_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


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
        svg_rect(20, 20, width - 40, height - 40, "#ffffff", radius=28, stroke="#dbe4f0"),
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
        svg_rect(20, 20, width - 40, height - 40, "#ffffff", radius=28, stroke="#dbe4f0"),
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
    export_yaml(summary)
    render_overview(summary)
    render_main_chart(summary)
    render_extension_chart(summary)
    print("Wrote results/summary.yaml")
    print("Wrote results/main_benchmark.yaml")
    print("Wrote results/extension_slices.yaml")
    print("Wrote figures/fork_results_overview_gpt_5_4_medium.svg")
    print("Wrote figures/fork_acb_full_gpt_5_4_medium.svg")
    print("Wrote figures/fork_extension_languages_gpt_5_4_medium.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
