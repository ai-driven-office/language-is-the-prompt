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

    main_langs = summary["main_benchmark"]["languages"]
    ranked = sorted(
        (
            {
                "language": language,
                "pass_rate": values["pass_rate"],
                "passed": values["passed"],
                "total": values["total"],
            }
            for language, values in main_langs.items()
        ),
        key=lambda item: (-item["pass_rate"], item["language"]),
    )

    guidance = {
        "gpt_5_4_medium": {
            "status": "verified",
            "recommended_languages": [row["language"] for row in ranked if row["pass_rate"] >= 60.0],
            "solid_languages": [row["language"] for row in ranked if 50.0 <= row["pass_rate"] < 60.0],
            "watchout_languages": [row["language"] for row in ranked if row["pass_rate"] < 50.0],
            "top5": ranked[:5],
        },
        "opus_4_6": {
            "status": "pending_benchmark",
            "notes": "No verified local Opus 4.6 benchmark results are published in this fork yet."
        }
    }
    write_yaml(RESULTS_DIR / "model_guidance.yaml", guidance)


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


def render_language_guide(summary: dict) -> None:
    width = 1400
    height = 860
    main_langs = summary["main_benchmark"]["languages"]
    ranked = sorted(
        (
            {
                "language": language,
                "pass_rate": values["pass_rate"],
            }
            for language, values in main_langs.items()
        ),
        key=lambda item: (-item["pass_rate"], item["language"]),
    )
    recommended = [row for row in ranked if row["pass_rate"] >= 60.0]
    solid = [row for row in ranked if 50.0 <= row["pass_rate"] < 60.0]
    watchouts = [row for row in ranked if row["pass_rate"] < 50.0]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<linearGradient id="guidebg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#f8fafc"/>',
        '<stop offset="100%" stop-color="#ecfeff"/>',
        "</linearGradient>",
        "</defs>",
        '<rect width="100%" height="100%" fill="url(#guidebg)"/>',
        svg_text(60, 72, "Language Guide for This Fork", size=38, weight="700"),
        svg_text(60, 108, "Verified guidance for GPT-5.4 Medium, plus an Opus 4.6 slot reserved for the next benchmark.", size=19, fill="#475569"),
    ]

    # GPT card
    parts.append(svg_rect(50, 150, 860, 650, "#ffffff", radius=32, stroke="#dbe4f0"))
    parts.append(svg_text(80, 198, "GPT-5.4 Medium", size=28, weight="700"))
    parts.append(svg_text(80, 228, "Verified local run on ACB-Full: 2088 / 3920 (53.3%)", size=16, fill="#475569"))

    sections = [
        ("Best fit", recommended, "#0f766e"),
        ("Solid", solid, "#2563eb"),
        ("Watchouts", watchouts, "#d97706"),
    ]
    base_y = 280
    for title, rows, color in sections:
        parts.append(svg_text(80, base_y, title, size=22, weight="700", fill=color))
        pill_x = 80
        pill_y = base_y + 24
        for row in rows:
            label = f'{row["language"]} {row["pass_rate"]:.1f}%'
            pill_width = max(120, 18 + len(label) * 10)
            if pill_x + pill_width > 850:
                pill_x = 80
                pill_y += 44
            parts.append(svg_rect(pill_x, pill_y, pill_width, 30, "#f8fafc", radius=15, stroke=color))
            parts.append(svg_text(pill_x + 14, pill_y + 20, label, size=14, weight="600", fill="#1f2937"))
            pill_x += pill_width + 12
        base_y = pill_y + 80

    # Opus card
    parts.append(svg_rect(950, 150, 400, 650, "#ffffff", radius=32, stroke="#dbe4f0"))
    parts.append(svg_text(980, 198, "Opus 4.6", size=28, weight="700"))
    parts.append(svg_text(980, 228, "Pending benchmark", size=18, weight="700", fill="#b45309"))
    parts.append(svg_text(980, 276, "No verified local results are published", size=16, fill="#475569"))
    parts.append(svg_text(980, 300, "for Opus 4.6 in this fork yet.", size=16, fill="#475569"))
    parts.append(svg_rect(980, 344, 340, 140, "#fff7ed", radius=24, stroke="#fdba74"))
    parts.append(svg_text(1008, 382, "What this means:", size=18, weight="700", fill="#9a3412"))
    parts.append(svg_text(1008, 416, "Use the GPT-5.4 guidance today.", size=15, fill="#7c2d12"))
    parts.append(svg_text(1008, 442, "Replace this card with verified Opus", size=15, fill="#7c2d12"))
    parts.append(svg_text(1008, 468, "tiers after the Anthropic run completes.", size=15, fill="#7c2d12"))
    parts.append(svg_rect(980, 528, 340, 180, "#f8fafc", radius=24, stroke="#cbd5e1"))
    parts.append(svg_text(1008, 566, "Next step", size=18, weight="700"))
    parts.append(svg_text(1008, 600, "Run the same local pipeline with", size=15, fill="#475569"))
    parts.append(svg_text(1008, 626, "the exact Opus 4.6 model id and", size=15, fill="#475569"))
    parts.append(svg_text(1008, 652, "publish the resulting YAML/JSON", size=15, fill="#475569"))
    parts.append(svg_text(1008, 678, "through the same summaries.", size=15, fill="#475569"))

    parts.append("</svg>")
    (FIGURES_DIR / "fork_model_language_guide.svg").write_text("\n".join(parts), encoding="utf-8")


def render_share_card(summary: dict) -> None:
    main_langs = summary["main_benchmark"]["languages"]
    ranked = sorted(
        (
            {
                "language": language,
                "pass_rate": values["pass_rate"],
            }
            for language, values in main_langs.items()
        ),
        key=lambda item: (-item["pass_rate"], item["language"]),
    )
    top = ranked[:8]
    width = 1600
    height = 900
    max_rate = max(row["pass_rate"] for row in top)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<linearGradient id="sharebg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#eff6ff"/>',
        '<stop offset="55%" stop-color="#f8fafc"/>',
        '<stop offset="100%" stop-color="#fefce8"/>',
        "</linearGradient>",
        "</defs>",
        '<rect width="100%" height="100%" fill="url(#sharebg)"/>',
        svg_rect(44, 44, 1512, 812, "#ffffff", radius=36, stroke="#dbe4f0"),
        svg_text(88, 122, "AutoCodeBenchmark Fork Snapshot", size=28, weight="700", fill="#0f172a"),
        svg_text(88, 170, "GPT-5.4 Medium language guidance", size=50, weight="700", fill="#1d4ed8"),
        svg_text(88, 212, "Verified local run on ACB-Full: 2088 / 3920 passed (53.3%)", size=22, weight="600", fill="#334155"),
        svg_text(88, 248, "Best current choices in this fork: Elixir, Kotlin, C#, Ruby, Julia. Opus 4.6 is marked pending until a verified local run exists.", size=18, fill="#475569"),
        svg_rect(1030, 92, 438, 170, "#f8fafc", radius=28, stroke="#cbd5e1"),
        svg_text(1064, 146, "Fork-only extensions", size=24, weight="700"),
        svg_text(1064, 184, "TypeScript + Effect: 53.6%", size=18, fill="#334155"),
        svg_text(1064, 214, "Lean4: 28.8% on validated rows", size=18, fill="#334155"),
        svg_text(1064, 244, "Gleam: 20.5% on validated rows", size=18, fill="#334155"),
    ]

    left = 88
    top_y = 330
    bar_left = 420
    bar_width = 460
    bar_height = 36
    parts.append(svg_text(left, top_y - 30, "Top verified languages for GPT-5.4 Medium", size=28, weight="700"))
    for index, row in enumerate(top):
        y = top_y + index * 58
        width_px = int(bar_width * row["pass_rate"] / max_rate)
        color = "#0f766e" if index < 3 else "#2563eb"
        parts.append(svg_text(left, y + 24, row["language"], size=22, weight="600"))
        parts.append(svg_rect(bar_left, y, bar_width, bar_height, "#e2e8f0", radius=18))
        parts.append(svg_rect(bar_left, y, width_px, bar_height, color, radius=18))
        parts.append(svg_text(bar_left + bar_width + 18, y + 24, f'{row["pass_rate"]:.1f}%', size=20, weight="700", fill=color))

    parts.append(svg_rect(980, 330, 488, 420, "#fff7ed", radius=32, stroke="#fdba74"))
    parts.append(svg_text(1016, 382, "How to read this", size=28, weight="700", fill="#9a3412"))
    parts.append(svg_text(1016, 430, "Use the ranked GPT-5.4 list for immediate language choice.", size=18, fill="#7c2d12"))
    parts.append(svg_text(1016, 466, "Elixir and Kotlin are the standout verified picks in this fork.", size=18, fill="#7c2d12"))
    parts.append(svg_text(1016, 502, "C#, Ruby, and Julia are also comfortably above the pack.", size=18, fill="#7c2d12"))
    parts.append(svg_text(1016, 556, "Opus 4.6", size=26, weight="700", fill="#7c2d12"))
    parts.append(svg_text(1016, 594, "Status: pending benchmark", size=20, weight="700", fill="#b45309"))
    parts.append(svg_text(1016, 628, "This fork does not publish an Opus recommendation until", size=17, fill="#7c2d12"))
    parts.append(svg_text(1016, 656, "the same local pipeline has been run and validated.", size=17, fill="#7c2d12"))
    parts.append(svg_text(88, 818, "Repo: ai-driven-office/AutoCodeBenchmark  |  Data: results/*.json, *.csv, *.yaml  |  Snapshot date: 2026-03-11", size=18, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_leaderboard_share_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


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
    render_language_guide(summary)
    render_share_card(summary)
    render_main_chart(summary)
    render_extension_chart(summary)
    print("Wrote results/summary.yaml")
    print("Wrote results/main_benchmark.yaml")
    print("Wrote results/extension_slices.yaml")
    print("Wrote results/model_guidance.yaml")
    print("Wrote figures/fork_results_overview_gpt_5_4_medium.svg")
    print("Wrote figures/fork_model_language_guide.svg")
    print("Wrote figures/fork_leaderboard_share_gpt_5_4_medium.svg")
    print("Wrote figures/fork_acb_full_gpt_5_4_medium.svg")
    print("Wrote figures/fork_extension_languages_gpt_5_4_medium.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
