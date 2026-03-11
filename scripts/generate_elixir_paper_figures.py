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
FACTORIAL_JSON = REPO_ROOT / "results" / "explicit_task_factorial" / "factorial_stats.json"
ROBUSTNESS_JSON = REPO_ROOT / "results" / "elixir_quick_robustness" / "robustness.json"

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


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def svg_wrapped_text(
    x: float,
    y: float,
    text: str,
    *,
    max_width: float,
    size: int = 16,
    weight: str = "500",
    fill: str = TEXT,
    anchor: str = "start",
    line_height: float | None = None,
) -> tuple[str, int]:
    line_height = line_height or size * 1.24
    max_chars = max(10, int(max_width / max(size * 0.56, 1)))
    lines = wrap_text(text, max_chars)
    safe_lines = [
        line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for line in lines
    ]
    spans = []
    for idx, line in enumerate(safe_lines):
        dy = "0" if idx == 0 else str(line_height)
        spans.append(f'<tspan x="{x}" dy="{dy}">{line}</tspan>')
    element = (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        + "".join(spans)
        + "</text>"
    )
    return element, len(lines)


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
    title_y = 146
    subtitle_size = 20
    chart_width = 1000
    bar_h = 30
    gap = 12
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 1", size=22, weight="700", fill=ELIXIR),
    ]
    title, title_lines = svg_wrapped_text(
        72,
        title_y,
        "AutoCodeBench leaderboard reproduced with GPT-5.4 medium",
        max_width=width - 150,
        size=42,
        weight="800",
        line_height=46,
    )
    body.append(title)
    subtitle_y = title_y + title_lines * 46 + 8
    subtitle, subtitle_lines = svg_wrapped_text(
        72,
        subtitle_y,
        "Elixir remains the strongest outlier on the original 20-language benchmark.",
        max_width=width - 150,
        size=subtitle_size,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)
    top = subtitle_y + subtitle_lines * 26 + 24
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
    ]
    title, title_lines = svg_wrapped_text(
        72,
        146,
        "Suite A: documentation structure dominates examples alone",
        max_width=width - 150,
        size=40,
        weight="800",
        line_height=44,
    )
    body.append(title)
    subtitle_y = 146 + title_lines * 44 + 8
    subtitle, _ = svg_wrapped_text(
        72,
        subtitle_y,
        "Removing examples does nothing. Removing structure collapses pass rate by about 40 points.",
        max_width=width - 150,
        size=20,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)
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
    ]
    title, title_lines = svg_wrapped_text(
        72,
        146,
        "Exact-task panel: matched tasks still favor Python and TypeScript",
        max_width=width - 150,
        size=38,
        weight="800",
        line_height=42,
    )
    body.append(title)
    subtitle_y = 146 + title_lines * 42 + 8
    subtitle, subtitle_lines = svg_wrapped_text(
        72,
        subtitle_y,
        (
            f"Across 48 matched language-task pairs, examples improve "
            f"{paired_examples['left_only_wins']} and hurt {paired_examples['right_only_wins']} "
            f"(two-sided sign p = {paired_examples['sign_test_p']})."
        ),
        max_width=width - 150,
        size=20,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)
    top_offset = subtitle_y + subtitle_lines * 26 + 18
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
    callout_y = max(270, top_offset + 10)
    body.append(svg_rect(1020, callout_y, 280, 180, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(1050, callout_y + 50, "Matched-panel read", size=24, weight="800"))
    body.append(svg_text(1050, callout_y + 90, f"Elixir: {sum(by_language['elixir'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=ELIXIR))
    body.append(svg_text(1050, callout_y + 120, f"Python: {sum(by_language['python'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=BLUE))
    body.append(svg_text(1050, callout_y + 150, f"TypeScript: {sum(by_language['typescript'].values()) / len(conditions):.1f}%", size=18, weight="700", fill=ACCENT))
    body.append(svg_text(72, height - 56, "Source: results/explicit_task_panel/panel_stats.json", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_3_explicit_task_panel.svg", width, height, body)


def render_elixir_docs_pipeline() -> None:
    width = 1500
    height = 900
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 5", size=22, weight="700", fill=ELIXIR),
    ]
    title, title_lines = svg_wrapped_text(
        72,
        146,
        "Elixir documentation pipeline: source metadata to ecosystem-wide legibility",
        max_width=width - 150,
        size=38,
        weight="800",
        line_height=42,
    )
    body.append(title)
    subtitle_y = 146 + title_lines * 42 + 8
    subtitle, subtitle_lines = svg_wrapped_text(
        72,
        subtitle_y,
        "The documentation system is embedded in the toolchain rather than bolted on after the fact.",
        max_width=width - 150,
        size=20,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)

    box_y = subtitle_y + subtitle_lines * 26 + 42

    boxes = [
        (90, box_y, 230, 140, "Source attrs", "@moduledoc, @doc,\n@typedoc near code", "#ede9fe", ELIXIR),
        (360, box_y, 230, 140, "Compiled docs", "BEAM doc chunks\nCode.fetch_docs/1", "#dbeafe", BLUE),
        (630, box_y, 230, 140, "Executable examples", "doctest ties docs\nto runnable examples", "#ffedd5", ACCENT),
        (900, box_y, 230, 140, "Published docs", "ExDoc renders guides,\nAPIs, extras, grouping", "#ccfbf1", GREEN),
        (1170, box_y, 230, 140, "Shared surface", "HexDocs gives packages\na common public format", "#f3e8ff", ELIXIR),
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

    panel_y = box_y + 220
    body.append(svg_rect(90, panel_y, 1310, 250, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(126, panel_y + 52, "Why this may matter for model-facing quality", size=28, weight="800"))

    bullets = [
        "Documentation lives next to the API surface, which reduces lookup ambiguity.",
        "Examples can be executable, so narrative guidance is partially checked against running code.",
        "Public and internal surfaces are deliberately separated with doc attributes rather than informal comments.",
        "ExDoc and HexDocs standardize the presentation layer across many libraries, increasing ecosystem regularity.",
    ]
    y = panel_y + 102
    for bullet in bullets:
        body.append(svg_text(138, y, "•", size=24, weight="800", fill=ELIXIR))
        body.append(svg_text(162, y, bullet, size=20, fill=TEXT))
        y += 42

    body.append(svg_text(72, height - 56, "Sources: Elixir docs, ExUnit doctest, ExDoc, HexDocs", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_5_elixir_docs_pipeline.svg", width, height, body)


def render_explicit_task_factorial() -> None:
    if not FACTORIAL_JSON.exists():
        return
    stats = json.loads(FACTORIAL_JSON.read_text(encoding="utf-8"))
    condition_overall = {row["condition_id"]: row for row in stats["condition_overall"]}
    overall_effects = {row["factor"]: row for row in stats["main_effects"]}
    by_language_rows = stats["main_effects_by_language"]
    condition_ids = [
        "ff_0000",
        "ff_0011",
        "ff_0101",
        "ff_0110",
        "ff_1001",
        "ff_1010",
        "ff_1100",
        "ff_1111",
    ]
    factor_labels = {
        "docs_rich": "Docs",
        "examples": "Examples",
        "contracts_explicit": "Contracts",
        "state_guidance": "State flow",
    }
    languages = ["elixir", "python", "typescript"]
    language_colors = {
        "elixir": ELIXIR,
        "python": BLUE,
        "typescript": ACCENT,
    }
    width = 1540
    height = 1040
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 4", size=22, weight="700", fill=ELIXIR),
    ]
    title, title_lines = svg_wrapped_text(
        72,
        146,
        "Small factorial study: explicit contracts are the clearest portable gain",
        max_width=width - 150,
        size=38,
        weight="800",
        line_height=42,
    )
    body.append(title)
    subtitle_y = 146 + title_lines * 42 + 8
    subtitle, subtitle_lines = svg_wrapped_text(
        72,
        subtitle_y,
        "Eight-condition fractional factorial on 16 exact tasks x 3 languages. Contract wording survives Holm correction; examples remain directional.",
        max_width=width - 150,
        size=20,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)

    # Left panel: eight condition pass rates.
    left_x = 90
    left_y = subtitle_y + subtitle_lines * 26 + 36
    left_w = 670
    chart_h = 420
    bar_w = 58
    gap = 18
    for tick in range(0, 101, 20):
        y = left_y + chart_h - chart_h * tick / 100
        body.append(svg_line(left_x + 110, y, left_x + left_w - 30, y, stroke=GRID, dash="4 8"))
        body.append(svg_text(left_x + 96, y + 5, f"{tick}%", size=13, weight="700", fill=MUTED, anchor="end"))
    body.append(svg_text(left_x, left_y - 28, "Condition pass rates", size=24, weight="800"))
    for idx, condition_id in enumerate(condition_ids):
        row = condition_overall[condition_id]
        rate = float(row["pass_rate"])
        x = left_x + 120 + idx * (bar_w + gap)
        bar_h = chart_h * rate / 100.0
        fill = "url(#elixirgrad)" if idx in {4, 5, 6, 7} else ("url(#accentgrad)" if idx in {1, 2, 3, 7} else "#c7d2fe")
        body.append(svg_rect(x, left_y + chart_h - bar_h, bar_w, bar_h, fill, radius=18))
        body.append(svg_text(x + bar_w / 2, left_y + chart_h + 26, condition_id.replace("ff_", ""), size=12, weight="700", fill=MUTED, anchor="middle"))
        body.append(svg_text(x + bar_w / 2, left_y + chart_h - bar_h - 14, f"{rate:.1f}%", size=15, weight="800", anchor="middle"))

    legend_items = [
        ("first bit = docs", "#c7d2fe"),
        ("examples / contracts bits", ACCENT),
        ("higher-order rich conditions", ELIXIR),
    ]
    legend_y = left_y + chart_h + 82
    for idx, (label, color) in enumerate(legend_items):
        lx = left_x + idx * 210
        body.append(svg_rect(lx, legend_y - 14, 18, 18, color, radius=6))
        body.append(svg_text(lx + 28, legend_y, label, size=15, fill=MUTED))

    # Right top: overall factor effects.
    right_x = 860
    right_y = 260
    body.append(svg_text(right_x, right_y - 28, "Matched main effects", size=24, weight="800"))
    effect_scale = 240
    axis_y = right_y + 150
    body.append(svg_line(right_x + 180, axis_y - 90, right_x + 180, axis_y + 140, stroke=GRID, width=2))
    for tick, label in [(-0.3, "-0.3"), (-0.1, "-0.1"), (0.0, "0"), (0.1, "0.1"), (0.3, "0.3")]:
        y = axis_y - tick * effect_scale
        body.append(svg_line(right_x + 110, y, right_x + 460, y, stroke=GRID, dash="4 8"))
        body.append(svg_text(right_x + 96, y + 5, label, size=13, weight="700", fill=MUTED, anchor="end"))
    factors = ["docs_rich", "examples", "contracts_explicit", "state_guidance"]
    for idx, factor in enumerate(factors):
        row = overall_effects[factor]
        delta = float(row["matched_mean_delta"])
        x = right_x + 145 + idx * 80
        dot_y = axis_y - delta * effect_scale
        body.append(svg_line(x, axis_y, x, dot_y, stroke="#cbd5e1", width=4))
        body.append(f'<circle cx="{x}" cy="{dot_y}" r="16" fill="url(#bluegrad)"/>')
        body.append(svg_text(x, axis_y + 38, factor_labels[factor], size=14, weight="800", anchor="middle"))
        body.append(svg_text(x, dot_y - 20, f"{delta:+.3f}", size=14, weight="800", fill=TEXT, anchor="middle"))
        body.append(svg_text(x, dot_y + 34, f"p={row['sign_test_p']}", size=12, fill=MUTED, anchor="middle"))

    # Right bottom: by-language effect heat rows.
    table_x = 830
    table_y = 560
    body.append(svg_text(table_x, table_y - 24, "Per-language matched deltas", size=24, weight="800"))
    headers = ["Language", "Docs", "Examples", "Contracts", "State flow"]
    col_x = [table_x, table_x + 170, table_x + 290, table_x + 430, table_x + 580]
    for idx, header in enumerate(headers):
        body.append(svg_text(col_x[idx], table_y + 12, header, size=15, weight="800"))
    effect_map = {(row["scope"], row["factor"]): row for row in by_language_rows}
    for row_idx, language in enumerate(languages):
        y = table_y + 54 + row_idx * 64
        body.append(svg_rect(table_x - 10, y - 24, 640, 46, "#f8fafc", radius=14, stroke="#e5e7eb"))
        body.append(svg_text(col_x[0], y + 4, language.capitalize(), size=16, weight="800", fill=language_colors[language]))
        for col_idx, factor in enumerate(factors):
            row = effect_map[(language, factor)]
            delta = float(row["matched_mean_delta"])
            fill = "#dcfce7" if delta > 0 else ("#fee2e2" if delta < 0 else "#e2e8f0")
            body.append(svg_rect(col_x[col_idx + 1] - 12, y - 15, 92, 26, fill, radius=10))
            body.append(svg_text(col_x[col_idx + 1] + 34, y + 4, f"{delta:+.3f}", size=14, weight="800", anchor="middle"))

    body.append(svg_text(72, height - 56, "Source: results/explicit_task_factorial/factorial_stats.json", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_4_explicit_task_factorial.svg", width, height, body)


def render_quick_robustness() -> None:
    if not ROBUSTNESS_JSON.exists():
        return
    stats = json.loads(ROBUSTNESS_JSON.read_text(encoding="utf-8"))
    panel = stats["panel"]
    factorial = stats["factorial"]["effects"]

    width = 1560
    height = 980
    body: list[str] = [
        svg_rect(34, 34, width - 68, height - 68, CARD, radius=34, stroke="#e4e8f1"),
        svg_text(72, 96, "Figure 6", size=22, weight="700", fill=ELIXIR),
    ]
    title, title_lines = svg_wrapped_text(
        72,
        146,
        "Quick robustness checks: scoped panel signal, stable contract effect",
        max_width=width - 150,
        size=38,
        weight="800",
        line_height=42,
    )
    body.append(title)
    subtitle_y = 146 + title_lines * 42 + 8
    subtitle, subtitle_lines = svg_wrapped_text(
        72,
        subtitle_y,
        "The exact-task panel stays low-power, while the factorial contract effect remains positive under bootstrap and leave-one-out scans.",
        max_width=width - 150,
        size=20,
        fill=MUTED,
        line_height=26,
    )
    body.append(subtitle)

    def x_map(value: float, axis_x: float, axis_w: float, low: float, high: float) -> float:
        return axis_x + axis_w * (value - low) / (high - low)

    # Left card: explicit-task panel examples effect.
    left_x = 72
    left_y = subtitle_y + subtitle_lines * 26 + 36
    left_w = 520
    left_h = 640
    body.append(svg_rect(left_x, left_y, left_w, left_h, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(left_x + 32, left_y + 50, "Panel: examples vs baseline", size=28, weight="800"))
    body.append(svg_text(left_x + 32, left_y + 84, "Comparison: rich_contract_examples - baseline_compact", size=16, fill=MUTED))

    axis_x = left_x + 96
    axis_w = left_w - 150
    axis_y = left_y + 170
    low = -0.20
    high = 0.35
    for tick in [-0.2, -0.1, 0.0, 0.1, 0.2, 0.3]:
        x = x_map(tick, axis_x, axis_w, low, high)
        body.append(svg_line(x, axis_y - 24, x, axis_y + 280, stroke=GRID, dash="4 8"))
        body.append(svg_text(x, axis_y - 36, f"{tick:+.1f}", size=13, weight="700", fill=MUTED, anchor="middle"))
    rows = [
        ("Overall delta", panel["overall_delta"], panel["task_bootstrap_ci"][0], panel["task_bootstrap_ci"][1], ELIXIR),
    ]
    for item in panel["leave_one_language_out"]:
        rows.append((f"Drop {item['omitted']}", item["delta"], item["delta"], item["delta"], BLUE))
    for idx, (label, value, ci_low, ci_high, color) in enumerate(rows):
        y = axis_y + 40 + idx * 64
        body.append(svg_text(left_x + 32, y + 6, label, size=17, weight="700"))
        body.append(svg_line(x_map(ci_low, axis_x, axis_w, low, high), y, x_map(ci_high, axis_x, axis_w, low, high), y, stroke=color, width=8))
        body.append(f'<circle cx="{x_map(value, axis_x, axis_w, low, high)}" cy="{y}" r="10" fill="{color}"/>')
        body.append(svg_text(axis_x + axis_w + 18, y + 6, f"{value:+.3f}", size=15, weight="800", fill=color))

    callout_y = left_y + 470
    body.append(svg_rect(left_x + 24, callout_y, left_w - 48, 130, "#ffffff", radius=20, stroke="#e5e7eb"))
    body.append(svg_text(left_x + 48, callout_y + 40, "Read", size=22, weight="800"))
    body.append(svg_text(left_x + 48, callout_y + 74, "Bootstrap CI crosses zero, so the panel remains", size=17, fill=TEXT))
    body.append(svg_text(left_x + 48, callout_y + 102, "directional rather than decisive at this scale.", size=17, fill=TEXT))

    # Right card: factorial robustness forest.
    right_x = 632
    right_y = 240
    right_w = 856
    right_h = 640
    body.append(svg_rect(right_x, right_y, right_w, right_h, "#f8fafc", radius=28, stroke="#e5e7eb"))
    body.append(svg_text(right_x + 32, right_y + 50, "Factorial: overall main effects", size=28, weight="800"))
    body.append(svg_text(right_x + 32, right_y + 84, "Dot = overall delta, thick bar = task-bootstrap 95% CI, thin bar = leave-one-task-out range", size=16, fill=MUTED))

    axis2_x = right_x + 210
    axis2_w = right_w - 300
    axis2_y = right_y + 150
    low2 = -0.15
    high2 = 0.60
    for tick in [-0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        x = x_map(tick, axis2_x, axis2_w, low2, high2)
        body.append(svg_line(x, axis2_y - 24, x, axis2_y + 340, stroke=GRID, dash="4 8"))
        body.append(svg_text(x, axis2_y - 36, f"{tick:+.1f}", size=13, weight="700", fill=MUTED, anchor="middle"))

    factor_labels = {
        "docs_rich": "Docs enrichment",
        "examples": "Examples",
        "contracts_explicit": "Explicit contracts",
        "state_guidance": "State guidance",
    }
    factor_colors = {
        "docs_rich": BLUE,
        "examples": ACCENT,
        "contracts_explicit": ELIXIR,
        "state_guidance": "#64748b",
    }
    for idx, item in enumerate(factorial):
        y = axis2_y + 36 + idx * 82
        label = factor_labels[item["factor"]]
        lo_task = min(entry["delta"] for entry in item["leave_one_task_out"])
        hi_task = max(entry["delta"] for entry in item["leave_one_task_out"])
        ci_low, ci_high = item["task_bootstrap_ci"]
        value = item["overall_delta"]
        color = factor_colors[item["factor"]]

        body.append(svg_text(right_x + 32, y + 6, label, size=18, weight="800", fill=color))
        body.append(svg_line(x_map(lo_task, axis2_x, axis2_w, low2, high2), y, x_map(hi_task, axis2_x, axis2_w, low2, high2), y, stroke="#cbd5e1", width=3))
        body.append(svg_line(x_map(ci_low, axis2_x, axis2_w, low2, high2), y, x_map(ci_high, axis2_x, axis2_w, low2, high2), y, stroke=color, width=10))
        body.append(f'<circle cx="{x_map(value, axis2_x, axis2_w, low2, high2)}" cy="{y}" r="11" fill="{color}"/>')
        body.append(svg_text(axis2_x + axis2_w + 20, y + 6, f"{value:+.3f}", size=15, weight="800", fill=color))

    body.append(svg_rect(right_x + 32, right_y + 520, right_w - 64, 86, "#ffffff", radius=20, stroke="#e5e7eb"))
    body.append(svg_text(right_x + 56, right_y + 556, "Most stable result", size=21, weight="800", fill=ELIXIR))
    body.append(svg_text(right_x + 56, right_y + 586, "Explicit contracts stay positive under every task-omission and language-omission cut.", size=17, fill=TEXT))

    body.append(svg_text(72, height - 56, "Source: results/elixir_quick_robustness/robustness.json", size=16, fill=MUTED))
    write_svg(FIGURES_DIR / "figure_6_quick_robustness.svg", width, height, body)


def main() -> None:
    render_leaderboard()
    render_suite_a()
    render_explicit_task_panel()
    render_elixir_docs_pipeline()
    render_explicit_task_factorial()
    render_quick_robustness()
    print("Wrote paper/figures/figure_1_acb_leaderboard.svg")
    print("Wrote paper/figures/figure_2_suite_a_docs.svg")
    print("Wrote paper/figures/figure_3_explicit_task_panel.svg")
    print("Wrote paper/figures/figure_5_elixir_docs_pipeline.svg")
    if FACTORIAL_JSON.exists():
        print("Wrote paper/figures/figure_4_explicit_task_factorial.svg")
    if ROBUSTNESS_JSON.exists():
        print("Wrote paper/figures/figure_6_quick_robustness.svg")


if __name__ == "__main__":
    main()
