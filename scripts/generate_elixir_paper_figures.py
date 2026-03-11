#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = REPO_ROOT / "paper" / "figures"
ACB_CSV = REPO_ROOT / "results" / "acb_full_openai_gpt_5_4_medium.csv"
ABLATION_CSV = REPO_ROOT / "results" / "elixir_active_suites" / "combined_summary.csv"
PANEL_JSON = REPO_ROOT / "results" / "explicit_task_panel" / "panel_stats.json"

BG = "#f7f7fb"
CARD = "#ffffff"
GRID = "#dde1ea"
TEXT = "#142033"
MUTED = "#58647a"
ELIXIR = "#7c3aed"
ACCENT = "#f97316"
BLUE = "#2563eb"
GREEN = "#0f766e"
GRAYBAR = "#cbd5e1"
FONT = "'Avenir Next', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def svg_text(x: float, y: float, text: str, *, size: int = 16, weight: str = "500", fill: str = TEXT, anchor: str = "start") -> str:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{safe}</text>'


def svg_rect(x: float, y: float, width: float, height: float, fill: str, *, radius: float = 16, stroke: str = "none", opacity: float = 1.0) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" opacity="{opacity}"/>'
    )


def svg_line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = GRID, width: float = 1.0, dash: str = "") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def svg_defs() -> str:
    return """
<defs>
  <linearGradient id="bggrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#fbfbff"/>
    <stop offset="100%" stop-color="#eef2ff"/>
  </linearGradient>
  <linearGradient id="elixirgrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#7c3aed"/>
    <stop offset="100%" stop-color="#a78bfa"/>
  </linearGradient>
  <linearGradient id="accentgrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#f97316"/>
    <stop offset="100%" stop-color="#fb7185"/>
  </linearGradient>
  <linearGradient id="bluegrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#2563eb"/>
    <stop offset="100%" stop-color="#60a5fa"/>
  </linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="18" stdDeviation="24" flood-color="#8b9ab7" flood-opacity="0.18"/>
  </filter>
</defs>
"""


def write_svg(path: Path, width: int, height: int, body: list[str]) -> None:
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append(svg_defs())
    parts.append(svg_rect(0, 0, width, height, "url(#bggrad)", radius=0))
    parts.extend(body)
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def render_leaderboard() -> None:
    rows = load_csv(ACB_CSV)
    data = sorted(
        [
            {
                "language": row["language"],
                "pass_rate": float(row["pass_rate"]),
            }
            for row in rows
        ],
        key=lambda item: item["pass_rate"],
        reverse=True,
    )
    width = 1500
    height = 1180
    left = 190
    top = 210
    chart_width = 1000
    bar_h = 30
    gap = 18
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 1", size=22, weight="700", fill=ELIXIR),
        svg_text(72, 146, "AutoCodeBench leaderboard reproduced with GPT-5.4 medium", size=42, weight="800"),
        svg_text(72, 184, "Elixir remains the strongest outlier on the original 20-language benchmark.", size=20, fill=MUTED),
    ]
    for tick in range(0, 101, 20):
        x = left + chart_width * tick / 100
        body.append(svg_line(x, top - 10, x, top + (bar_h + gap) * len(data), stroke=GRID, dash="4 8"))
        body.append(svg_text(x, top - 24, f"{tick}%", size=13, weight="700", fill=MUTED, anchor="middle"))
    for idx, row in enumerate(data):
        y = top + idx * (bar_h + gap)
        fill = "url(#elixirgrad)" if row["language"] == "elixir" else GRAYBAR
        label_fill = ELIXIR if row["language"] == "elixir" else TEXT
        bar_w = chart_width * row["pass_rate"] / 100.0
        body.append(svg_text(72, y + 22, f"{idx + 1}.", size=16, weight="700", fill=MUTED))
        body.append(svg_text(112, y + 22, row["language"], size=17, weight="800", fill=label_fill))
        body.append(svg_rect(left, y, chart_width, bar_h, "#eef2f8", radius=15))
        body.append(svg_rect(left, y, bar_w, bar_h, fill, radius=15))
        body.append(svg_text(left + chart_width + 18, y + 22, f"{row['pass_rate']:.1f}%", size=17, weight="800", fill=label_fill))
    body.append(svg_text(72, height - 56, "Source: results/acb_full_openai_gpt_5_4_medium.csv", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_1_acb_leaderboard.svg", width, height, body)


def render_suite_a() -> None:
    rows = load_csv(ABLATION_CSV)
    suite_rows = [row for row in rows if row["suite_id"] == "suite_a"]
    order = ["full_docs", "reference_no_examples", "minimal_docs", "signature_only"]
    labels = {
        "full_docs": "Full docs",
        "reference_no_examples": "No examples",
        "minimal_docs": "Minimal docs",
        "signature_only": "Signature only",
    }
    data = {row["condition"]: row for row in suite_rows}
    width = 1300
    height = 920
    left = 120
    base_y = 730
    chart_h = 470
    chart_w = 1040
    bar_w = 180
    gap = 70
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 2", size=22, weight="700", fill=ELIXIR),
        svg_text(72, 146, "Suite A: documentation structure dominates examples alone", size=40, weight="800"),
        svg_text(72, 184, "Removing examples does nothing. Removing structure collapses pass rate by about 40 points.", size=20, fill=MUTED),
    ]
    for tick in range(0, 101, 20):
        y = base_y - chart_h * tick / 100
        body.append(svg_line(left, y, left + chart_w, y, stroke=GRID, dash="4 8"))
        body.append(svg_text(left - 14, y + 5, f"{tick}%", size=13, weight="700", fill=MUTED, anchor="end"))
    for idx, key in enumerate(order):
        row = data[key]
        rate = float(row["pass_rate"])
        x = left + 60 + idx * (bar_w + gap)
        bar_h = chart_h * rate / 100.0
        fill = "url(#elixirgrad)" if key in {"full_docs", "reference_no_examples"} else "url(#accentgrad)"
        body.append(svg_rect(x, base_y - bar_h, bar_w, bar_h, fill, radius=24))
        body.append(svg_text(x + bar_w / 2, base_y + 38, labels[key], size=18, weight="700", anchor="middle"))
        body.append(svg_text(x + bar_w / 2, base_y - bar_h - 16, f"{rate:.1f}%", size=20, weight="800", fill=TEXT, anchor="middle"))
        if key in {"minimal_docs", "signature_only"}:
            delta = float(row["delta_vs_baseline"])
            body.append(svg_text(x + bar_w / 2, base_y - bar_h - 42, f"{delta:.1f} pp", size=15, weight="700", fill=ACCENT, anchor="middle"))
    body.append(svg_text(72, height - 56, "Source: results/elixir_active_suites/combined_summary.csv", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_2_suite_a_docs.svg", width, height, body)


def render_explicit_task_panel() -> None:
    panel = json.loads(PANEL_JSON.read_text(encoding="utf-8"))
    overall = sorted(panel["overall"], key=lambda row: (row["language"], row["condition_id"]))
    paired_examples = next(
        row
        for row in panel["paired"]
        if row["comparison"] == "rich_contract_examples_vs_baseline_compact"
    )
    by_language: dict[str, dict[str, float]] = {}
    for row in overall:
        by_language.setdefault(row["language"], {})[row["condition_id"]] = row["pass_rate"]
    languages = ["elixir", "python", "typescript"]
    conditions = ["baseline_compact", "rich_contract", "rich_contract_examples"]
    cond_labels = {
        "baseline_compact": "Baseline",
        "rich_contract": "Contract",
        "rich_contract_examples": "Contract + examples",
    }
    colors = {
        "baseline_compact": "#a5b4fc",
        "rich_contract": BLUE,
        "rich_contract_examples": ACCENT,
    }
    width = 1420
    height = 980
    left = 120
    base_y = 760
    chart_h = 500
    group_w = 300
    bar_w = 72
    inner_gap = 24
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 3", size=22, weight="700", fill=ELIXIR),
        svg_text(72, 146, "Exact-task panel: matched tasks still favor Python and TypeScript", size=38, weight="800"),
        svg_text(
            72,
            184,
            (
                f"Across 48 matched language-task pairs, examples improve "
                f"{paired_examples['left_only_wins']} and hurt {paired_examples['right_only_wins']} "
                f"(two-sided sign p = {paired_examples['sign_test_p']})."
            ),
            size=20,
            fill=MUTED,
        ),
    ]
    for tick in range(0, 101, 20):
        y = base_y - chart_h * tick / 100
        body.append(svg_line(left, y, width - 120, y, stroke=GRID, dash="4 8"))
        body.append(svg_text(left - 14, y + 5, f"{tick}%", size=13, weight="700", fill=MUTED, anchor="end"))
    for idx, language in enumerate(languages):
        group_x = left + 90 + idx * (group_w + 90)
        body.append(svg_text(group_x + group_w / 2, base_y + 58, language.capitalize(), size=20, weight="800", anchor="middle"))
        for cond_idx, condition in enumerate(conditions):
            rate = by_language[language][condition]
            x = group_x + cond_idx * (bar_w + inner_gap)
            bar_h = chart_h * rate / 100.0
            body.append(svg_rect(x, base_y - bar_h, bar_w, bar_h, colors[condition], radius=18))
            body.append(svg_text(x + bar_w / 2, base_y - bar_h - 14, f"{rate:.1f}%", size=16, weight="800", anchor="middle"))
            body.append(svg_text(x + bar_w / 2, base_y + 28, cond_labels[condition], size=13, weight="700", fill=MUTED, anchor="middle"))
    body.append(svg_rect(1020, 270, 280, 180, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(1050, 320, "Matched-panel read", size=24, weight="800"))
    body.append(svg_text(1050, 360, f"Elixir: {sum(by_language['elixir'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=ELIXIR))
    body.append(svg_text(1050, 390, f"Python: {sum(by_language['python'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=BLUE))
    body.append(svg_text(1050, 420, f"TypeScript: {sum(by_language['typescript'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=ACCENT))
    body.append(svg_text(72, height - 56, "Source: results/explicit_task_panel/panel_stats.json", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_3_explicit_task_panel.svg", width, height, body)


def render_elixir_docs_pipeline() -> None:
    width = 1500
    height = 900
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 4", size=22, weight="700", fill=ELIXIR),
        svg_text(72, 146, "Elixir documentation pipeline: source metadata to ecosystem-wide legibility", size=38, weight="800"),
        svg_text(72, 184, "The documentation system is embedded in the toolchain rather than bolted on after the fact.", size=20, fill=MUTED),
    ]

    boxes = [
        (90, 280, 230, 140, "Source attrs", "@moduledoc, @doc,\n@typedoc near code", "#ede9fe", ELIXIR),
        (360, 280, 230, 140, "Compiled docs", "BEAM doc chunks\nCode.fetch_docs/1", "#dbeafe", BLUE),
        (630, 280, 230, 140, "Executable examples", "doctest ties docs\nto runnable examples", "#ffedd5", ACCENT),
        (900, 280, 230, 140, "Published docs", "ExDoc renders guides,\nAPIs, extras, grouping", "#ccfbf1", GREEN),
        (1170, 280, 230, 140, "Shared surface", "HexDocs gives packages\na common public format", "#f3e8ff", ELIXIR),
    ]

    for x, y, w, h, title, subtitle, fill, accent in boxes:
        body.append(svg_rect(x, y, w, h, fill, radius=28, stroke="#d7dce7"))
        body.append(svg_text(x + 24, y + 44, title, size=24, weight="800", fill=accent))
        sub1, sub2 = subtitle.split("\n")
        body.append(svg_text(x + 24, y + 84, sub1, size=18, fill=TEXT))
        body.append(svg_text(x + 24, y + 112, sub2, size=18, fill=TEXT))

    for idx in range(len(boxes) - 1):
        x1 = boxes[idx][0] + boxes[idx][2]
        x2 = boxes[idx + 1][0]
        y = boxes[idx][1] + boxes[idx][3] / 2
        body.append(svg_line(x1 + 16, y, x2 - 16, y, stroke="#94a3b8", width=4))
        body.append(
            f'<polygon points="{x2 - 16},{y} {x2 - 34},{y - 10} {x2 - 34},{y + 10}" fill="#94a3b8"/>'
        )

    body.append(svg_rect(90, 500, 1310, 250, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(126, 552, "Why this may matter for model-facing quality", size=28, weight="800"))

    bullets = [
        "Documentation lives next to the API surface, which reduces lookup ambiguity.",
        "Examples can be executable, so narrative guidance is partially checked against running code.",
        "Public and internal surfaces are deliberately separated with doc attributes rather than informal comments.",
        "ExDoc and HexDocs standardize the presentation layer across many libraries, increasing ecosystem regularity.",
    ]
    y = 602
    for bullet in bullets:
        body.append(svg_text(138, y, "•", size=24, weight="800", fill=ELIXIR))
        body.append(svg_text(162, y, bullet, size=20, fill=TEXT))
        y += 42

    body.append(svg_text(72, height - 56, "Sources: Elixir docs, ExUnit doctest, ExDoc, HexDocs", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_4_elixir_docs_pipeline.svg", width, height, body)


def main() -> None:
    render_leaderboard()
    render_suite_a()
    render_explicit_task_panel()
    render_elixir_docs_pipeline()
    print("Wrote paper/figures/figure_1_acb_leaderboard.svg")
    print("Wrote paper/figures/figure_2_suite_a_docs.svg")
    print("Wrote paper/figures/figure_3_explicit_task_panel.svg")
    print("Wrote paper/figures/figure_4_elixir_docs_pipeline.svg")


if __name__ == "__main__":
    main()
