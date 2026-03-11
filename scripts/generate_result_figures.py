#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "results" / "summary.json"
FIGURES_DIR = REPO_ROOT / "figures"
RESULTS_DIR = REPO_ROOT / "results"
FONT_STACK = "'Space Grotesk','Avenir Next','Inter','Segoe UI',sans-serif"
BODY_STACK = "'DM Sans','Inter','Segoe UI',sans-serif"


def load_summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def svg_text(
    x: int | float,
    y: int | float,
    text: object,
    *,
    size: int = 16,
    weight: str = "400",
    fill: str = "#0f172a",
    family: str = BODY_STACK,
    anchor: str | None = None,
    opacity: float | None = None,
) -> str:
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'font-family="{family}"',
        f'font-size="{size}"',
        f'font-weight="{weight}"',
        f'fill="{fill}"',
    ]
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    return f"<text {' '.join(attrs)}>{esc(text)}</text>"


def svg_rect(
    x: int | float,
    y: int | float,
    width: int | float,
    height: int | float,
    fill: str,
    *,
    radius: int | float = 24,
    stroke: str | None = None,
    stroke_width: int | float = 1,
    opacity: float | None = None,
    extra: str = "",
) -> str:
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'width="{width}"',
        f'height="{height}"',
        f'rx="{radius}"',
        f'fill="{fill}"',
    ]
    if stroke:
        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{stroke_width}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if extra:
        attrs.append(extra.strip())
    return f"<rect {' '.join(attrs)}/>"


def svg_circle(cx: int | float, cy: int | float, r: int | float, fill: str, *, opacity: float = 1.0, extra: str = "") -> str:
    attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"', f'fill="{fill}"', f'opacity="{opacity}"']
    if extra:
        attrs.append(extra.strip())
    return f"<circle {' '.join(attrs)}/>"


def scalar_yaml(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    special = [":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", ">", "%", "@", "`", "\"", "'"]
    if text == "" or any(ch in text for ch in special) or text.strip() != text:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def dump_yaml(value: object, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(dump_yaml(item, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {scalar_yaml(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(dump_yaml(item, indent + 1))
            else:
                lines.append(f"{prefix}- {scalar_yaml(item)}")
        return lines
    return [f"{prefix}{scalar_yaml(value)}"]


def write_yaml(path: Path, payload: object) -> None:
    path.write_text("\n".join(dump_yaml(payload)) + "\n", encoding="utf-8")


def combined_language_rows(summary: dict) -> list[dict]:
    rows: list[dict] = []
    for language, values in summary["main_benchmark"]["languages"].items():
        rows.append(
            {
                "language": language,
                "pass_rate": values["pass_rate"],
                "passed": values["passed"],
                "denominator": values["total"],
                "basis": "ACB-Full",
                "basis_tag": "FULL",
                "basis_detail": f'{values["passed"]}/{values["total"]}',
                "kind": "full",
            }
        )

    ext = summary["extension_slices"]
    rows.extend(
        [
            {
                "language": "typescript_effect",
                "pass_rate": ext["typescript_effect"]["pass_rate"],
                "passed": ext["typescript_effect"]["passed"],
                "denominator": ext["typescript_effect"]["source_rows"],
                "basis": "translated slice",
                "basis_tag": "SLICE",
                "basis_detail": f'{ext["typescript_effect"]["passed"]}/{ext["typescript_effect"]["source_rows"]}',
                "kind": "slice",
            },
            {
                "language": "lean4",
                "pass_rate": ext["lean4"]["pass_rate_on_validated_rows"],
                "passed": ext["lean4"]["passed"],
                "denominator": ext["lean4"]["validated_rows"],
                "basis": "validated subset",
                "basis_tag": "VALIDATED",
                "basis_detail": f'{ext["lean4"]["passed"]}/{ext["lean4"]["validated_rows"]}',
                "kind": "validated",
            },
            {
                "language": "gleam",
                "pass_rate": ext["gleam"]["pass_rate_on_validated_rows"],
                "passed": ext["gleam"]["passed"],
                "denominator": ext["gleam"]["validated_rows"],
                "basis": "validated subset",
                "basis_tag": "VALIDATED",
                "basis_detail": f'{ext["gleam"]["passed"]}/{ext["gleam"]["validated_rows"]}',
                "kind": "validated",
            },
        ]
    )
    return sorted(rows, key=lambda row: (-row["pass_rate"], row["language"]))


def tier_name(pass_rate: float) -> str:
    if pass_rate >= 70:
        return "Elite"
    if pass_rate >= 55:
        return "Strong"
    if pass_rate >= 45:
        return "Capable"
    return "Emerging"


def tier_color(name: str) -> str:
    return {
        "Elite": "#14b8a6",
        "Strong": "#3b82f6",
        "Capable": "#8b5cf6",
        "Emerging": "#f97316",
    }[name]


def basis_colors(kind: str) -> tuple[str, str]:
    return {
        "full": ("#dbeafe", "#1d4ed8"),
        "validated": ("#fef3c7", "#b45309"),
        "slice": ("#ede9fe", "#6d28d9"),
    }[kind]


def make_guidance(summary: dict) -> dict:
    rows = combined_language_rows(summary)
    tiers: dict[str, list[dict]] = {"elite": [], "strong": [], "capable": [], "emerging": []}
    for row in rows:
        bucket = tier_name(row["pass_rate"]).lower()
        tiers[bucket].append(
            {
                "language": row["language"],
                "pass_rate": row["pass_rate"],
                "basis": row["basis"],
                "basis_tag": row["basis_tag"],
            }
        )
    return {
        "gpt_5_4_medium": {
            "status": "verified",
            "snapshot_date": "2026-03-11",
            "overall_acb_full_pass_rate": summary["main_benchmark"]["pass_rate"],
            "highlight_languages": [row["language"] for row in rows[:5]],
            "tiers": tiers,
            "all_languages": rows,
            "notes": [
                "FULL rows come from the original ACB-Full benchmark.",
                "VALIDATED rows come from translated slices that passed canonical validation before model scoring.",
                "SLICE rows come from translated slices without that validation gate.",
            ],
        }
    }


def export_yaml(summary: dict) -> None:
    write_yaml(RESULTS_DIR / "summary.yaml", summary)
    write_yaml(RESULTS_DIR / "main_benchmark.yaml", summary["main_benchmark"])
    write_yaml(RESULTS_DIR / "extension_slices.yaml", summary["extension_slices"])
    write_yaml(RESULTS_DIR / "all_languages.yaml", {"languages": combined_language_rows(summary)})
    write_yaml(RESULTS_DIR / "model_guidance.yaml", make_guidance(summary))


def svg_defs() -> list[str]:
    return [
        "<defs>",
        '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#f8fbff"/>',
        '<stop offset="45%" stop-color="#f4f7ff"/>',
        '<stop offset="100%" stop-color="#fff8ef"/>',
        "</linearGradient>",
        '<linearGradient id="titlegrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#0f766e"/>',
        '<stop offset="50%" stop-color="#2563eb"/>',
        '<stop offset="100%" stop-color="#7c3aed"/>',
        "</linearGradient>",
        '<linearGradient id="cardgrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.98"/>',
        '<stop offset="100%" stop-color="#f8fafc" stop-opacity="0.92"/>',
        "</linearGradient>",
        '<linearGradient id="elitegrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#14b8a6"/>',
        '<stop offset="100%" stop-color="#0f766e"/>',
        "</linearGradient>",
        '<linearGradient id="stronggrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#60a5fa"/>',
        '<stop offset="100%" stop-color="#2563eb"/>',
        "</linearGradient>",
        '<linearGradient id="capablegrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#a78bfa"/>',
        '<stop offset="100%" stop-color="#7c3aed"/>',
        "</linearGradient>",
        '<linearGradient id="emerginggrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#fb923c"/>',
        '<stop offset="100%" stop-color="#ea580c"/>',
        "</linearGradient>",
        '<filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">',
        '<feDropShadow dx="0" dy="24" stdDeviation="24" flood-color="#94a3b8" flood-opacity="0.18"/>',
        "</filter>",
        '<filter id="softblur" x="-50%" y="-50%" width="200%" height="200%">',
        '<feGaussianBlur stdDeviation="36"/>',
        "</filter>",
        "</defs>",
    ]


def add_background(parts: list[str], width: int, height: int) -> None:
    parts.append(f'<rect width="{width}" height="{height}" fill="url(#bg)"/>')
    parts.append(svg_circle(220, 140, 150, "#93c5fd", opacity=0.28, extra='filter="url(#softblur)"'))
    parts.append(svg_circle(width - 180, 180, 170, "#c4b5fd", opacity=0.22, extra='filter="url(#softblur)"'))
    parts.append(svg_circle(width - 120, height - 130, 190, "#fdba74", opacity=0.18, extra='filter="url(#softblur)"'))
    parts.append(svg_circle(160, height - 120, 120, "#2dd4bf", opacity=0.12, extra='filter="url(#softblur)"'))


def render_overview(summary: dict) -> None:
    width = 1380
    height = 760
    ext = summary["extension_slices"]
    cards = [
        ("ACB-Full", "53.3%", "2088 / 3920", "20 benchmark languages", "#0f766e"),
        ("Top Picks", "5", "elixir, kotlin, csharp", "plus ruby and julia", "#2563eb"),
        ("Added Languages", "3", "gleam, lean4, typescript_effect", "folded into the new visuals", "#7c3aed"),
        ("Data Exports", "YAML", "summary, guidance, all_languages", "plus JSON and CSV files", "#ea580c"),
    ]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.extend(svg_defs())
    add_background(parts, width, height)
    parts.append(svg_rect(34, 34, width - 68, height - 68, "url(#cardgrad)", radius=36, stroke="#dbe4f0", extra='filter="url(#shadow)"'))
    parts.append(svg_text(72, 112, "AutoCodeBenchmark Fork Update", size=28, weight="700", family=FONT_STACK))
    parts.append(svg_text(72, 174, "GPT-5.4 Medium language snapshot", size=60, weight="800", fill="url(#titlegrad)", family=FONT_STACK))
    parts.append(svg_text(72, 220, "One launch-style view across the original benchmark and the added language tracks.", size=22, fill="#475569"))

    for idx, (title, value, line1, line2, color) in enumerate(cards):
        col = idx % 2
        row = idx // 2
        x = 72 + col * 620
        y = 290 + row * 190
        parts.append(svg_rect(x, y, 560, 150, "#ffffff", radius=28, stroke="#e2e8f0"))
        parts.append(svg_rect(x + 24, y + 26, 10, 98, color, radius=10))
        parts.append(svg_text(x + 56, y + 52, title, size=24, weight="700", family=FONT_STACK))
        parts.append(svg_text(x + 56, y + 98, value, size=40, weight="800", fill=color, family=FONT_STACK))
        parts.append(svg_text(x + 190, y + 90, line1, size=18, weight="600"))
        parts.append(svg_text(x + 190, y + 118, line2, size=16, fill="#64748b"))

    parts.append(svg_text(72, 676, "FULL, VALIDATED, and SLICE tags remain visible in the larger charts so the basis stays clear.", size=17, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_results_overview_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def add_stat_pill(
    parts: list[str],
    x: int,
    y: int,
    width: int,
    title: str,
    value: str,
    fill: str,
    *,
    value_size: int = 28,
) -> None:
    parts.append(svg_rect(x, y, width, 88, "#ffffff", radius=24, stroke="#dbe4f0"))
    parts.append(svg_text(x + 22, y + 34, title, size=15, weight="700", fill="#64748b", family=FONT_STACK))
    parts.append(svg_text(x + 22, y + 64, value, size=value_size, weight="800", fill=fill, family=FONT_STACK))


def render_tier_cards(parts: list[str], rows: list[dict], x: int, y: int, width: int, height: int, title: str) -> None:
    color = tier_color(title)
    gradient_id = title.lower() + "grad"
    parts.append(svg_rect(x, y, width, height, "#ffffff", radius=30, stroke="#e2e8f0"))
    parts.append(svg_rect(x + 18, y + 18, width - 36, 66, f"url(#{gradient_id})", radius=22, opacity=0.12))
    parts.append(svg_text(x + 28, y + 48, title, size=28, weight="800", fill=color, family=FONT_STACK))
    parts.append(svg_text(x + width - 28, y + 48, f"{len(rows)} languages", size=16, weight="700", fill="#64748b", anchor="end"))

    gap_x = 16
    card_w = (width - 3 * gap_x) / 2
    card_h = 64
    start_y = y + 102
    for idx, row in enumerate(rows):
        col = idx % 2
        row_idx = idx // 2
        card_x = x + gap_x + col * (card_w + gap_x)
        card_y = start_y + row_idx * 68
        bg_fill = "#fbfdff"
        stroke = "#dbe4f0"
        pill_fill, pill_text = basis_colors(row["kind"])
        parts.append(svg_rect(card_x, card_y, card_w, card_h, bg_fill, radius=20, stroke=stroke))
        pill_w = 66 if row["basis_tag"] == "FULL" else 94
        parts.append(svg_text(card_x + 16, card_y + 24, row["language"], size=17, weight="700", family=FONT_STACK))
        parts.append(svg_rect(card_x + card_w - pill_w - 14, card_y + 12, pill_w, 22, pill_fill, radius=11))
        parts.append(svg_text(card_x + card_w - pill_w / 2 - 14, card_y + 28, row["basis_tag"], size=11, weight="800", fill=pill_text, anchor="middle", family=FONT_STACK))
        parts.append(svg_text(card_x + 16, card_y + 48, row["basis_detail"], size=13, fill="#64748b"))
        parts.append(svg_text(card_x + card_w - 16, card_y + 49, f'{row["pass_rate"]:.1f}%', size=22, weight="800", fill=color, family=FONT_STACK, anchor="end"))


def render_language_guide(summary: dict) -> None:
    rows = combined_language_rows(summary)
    width = 1660
    height = 1260
    tiers = {
        "Elite": [row for row in rows if tier_name(row["pass_rate"]) == "Elite"],
        "Strong": [row for row in rows if tier_name(row["pass_rate"]) == "Strong"],
        "Capable": [row for row in rows if tier_name(row["pass_rate"]) == "Capable"],
        "Emerging": [row for row in rows if tier_name(row["pass_rate"]) == "Emerging"],
    }
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.extend(svg_defs())
    add_background(parts, width, height)
    parts.append(svg_rect(34, 34, width - 68, height - 68, "url(#cardgrad)", radius=40, stroke="#dbe4f0", extra='filter="url(#shadow)"'))
    parts.append(svg_text(72, 108, "Language Atlas", size=28, weight="700", family=FONT_STACK))
    parts.append(svg_text(72, 162, "GPT-5.4 Medium across", size=54, weight="800", fill="url(#titlegrad)", family=FONT_STACK))
    parts.append(svg_text(72, 214, "every language tracked in this fork", size=54, weight="800", fill="url(#titlegrad)", family=FONT_STACK))
    parts.append(svg_text(72, 252, "The 20 ACB-Full languages and the 3 added language tracks are shown together. Basis tags stay attached to every row.", size=22, fill="#475569"))
    add_stat_pill(parts, 72, 286, 270, "ACB-Full", "53.3% overall", "#0f766e", value_size=24)
    add_stat_pill(parts, 360, 286, 270, "Top verified", "elixir / kotlin / csharp", "#2563eb", value_size=18)
    add_stat_pill(parts, 648, 286, 270, "Added tracks", "ts_effect / lean4 / gleam", "#7c3aed", value_size=18)
    add_stat_pill(parts, 936, 286, 300, "Basis tags", "FULL | VALIDATED | SLICE", "#ea580c", value_size=18)

    render_tier_cards(parts, tiers["Elite"], 72, 412, 736, 318, "Elite")
    render_tier_cards(parts, tiers["Strong"], 852, 412, 736, 318, "Strong")
    render_tier_cards(parts, tiers["Capable"], 72, 764, 736, 406, "Capable")
    render_tier_cards(parts, tiers["Emerging"], 852, 764, 736, 406, "Emerging")

    parts.append(svg_text(72, 1210, "FULL = original benchmark language. VALIDATED = translated slice that passed canonical validation. SLICE = translated slice without that gate.", size=17, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_model_language_guide.svg").write_text("\n".join(parts), encoding="utf-8")


def render_share_card(summary: dict) -> None:
    rows = combined_language_rows(summary)
    width = 1600
    height = 980
    top_rows = rows[:12]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.extend(svg_defs())
    add_background(parts, width, height)
    parts.append(svg_rect(40, 40, width - 80, height - 80, "url(#cardgrad)", radius=40, stroke="#dbe4f0", extra='filter="url(#shadow)"'))
    parts.append(svg_text(78, 114, "AutoCodeBenchmark Fork Snapshot", size=28, weight="700", family=FONT_STACK))
    parts.append(svg_text(78, 176, "GPT-5.4 Medium language leaderboard", size=58, weight="800", fill="url(#titlegrad)", family=FONT_STACK))
    parts.append(svg_text(78, 220, "Latest verified local run in this fork. All tracked languages are folded into one visual.", size=22, fill="#475569"))
    add_stat_pill(parts, 78, 262, 260, "Overall", "53.3% on ACB-Full", "#0f766e", value_size=22)
    add_stat_pill(parts, 356, 262, 260, "Best fit", "elixir and kotlin", "#2563eb", value_size=22)
    add_stat_pill(parts, 634, 262, 290, "Added languages", "3 tracked extensions", "#7c3aed", value_size=22)
    add_stat_pill(parts, 944, 262, 290, "Data files", "JSON, CSV, YAML", "#ea580c", value_size=22)

    parts.append(svg_text(78, 402, "Top language tracks in this fork", size=30, weight="800", family=FONT_STACK))
    bar_left = 330
    bar_width = 530
    bar_height = 32
    max_rate = top_rows[0]["pass_rate"]
    for idx, row in enumerate(top_rows):
        y = 444 + idx * 38
        tier = tier_name(row["pass_rate"])
        color = tier_color(tier)
        fill, text = basis_colors(row["kind"])
        width_px = int(bar_width * row["pass_rate"] / max_rate)
        pill_w = 102 if row["basis_tag"] != "FULL" else 70
        parts.append(svg_text(78, y + 21, row["language"], size=17, weight="700", family=FONT_STACK))
        parts.append(svg_rect(210, y + 4, pill_w, 22, fill, radius=11))
        parts.append(svg_text(210 + pill_w / 2, y + 20, row["basis_tag"], size=11, weight="800", fill=text, anchor="middle", family=FONT_STACK))
        parts.append(svg_rect(bar_left, y, bar_width, bar_height, "#e2e8f0", radius=16))
        parts.append(svg_rect(bar_left, y, width_px, bar_height, f"url(#{tier.lower()}grad)", radius=16))
        parts.append(svg_text(bar_left + bar_width + 18, y + 23, f'{row["pass_rate"]:.1f}%', size=22, weight="800", fill=color, family=FONT_STACK))

    parts.append(svg_rect(970, 402, 552, 430, "#ffffff", radius=30, stroke="#e2e8f0"))
    parts.append(svg_text(1002, 454, "What stands out", size=30, weight="800", family=FONT_STACK))
    points = [
        ("Elixir, Kotlin, and C#", "form the clear top tier."),
        ("Ruby and Julia keep", "the strong tier broad."),
        ("TypeScript with Effect", "lands in the capable band."),
        ("Lean4 and Gleam are included,", "but still trail the pack."),
        ("Every non-FULL row stays tagged", "so the basis stays explicit."),
    ]
    for idx, (line1, line2) in enumerate(points):
        y = 504 + idx * 60
        parts.append(svg_circle(1020, y - 8, 8, "#2563eb"))
        parts.append(svg_text(1044, y - 4, line1, size=18, weight="700"))
        parts.append(svg_text(1044, y + 20, line2, size=18, fill="#475569"))

    parts.append(svg_text(78, 932, "Basis tags: FULL = ACB-Full language, VALIDATED = translated slice after canonical validation, SLICE = translated slice without that gate.", size=17, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_leaderboard_share_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def render_all_language_bars(summary: dict) -> None:
    rows = combined_language_rows(summary)
    width = 1520
    row_height = 40
    top = 168
    chart_left = 390
    chart_width = 820
    height = top + len(rows) * row_height + 120
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.extend(svg_defs())
    add_background(parts, width, height)
    parts.append(svg_rect(30, 30, width - 60, height - 60, "url(#cardgrad)", radius=36, stroke="#dbe4f0", extra='filter="url(#shadow)"'))
    parts.append(svg_text(66, 96, "All languages in this fork", size=30, weight="700", family=FONT_STACK))
    parts.append(svg_text(66, 146, "Sorted by pass rate, with FULL, VALIDATED, and SLICE rows shown together.", size=22, fill="#475569"))

    for tick in range(0, 101, 20):
        x = chart_left + chart_width * tick / 100
        parts.append(f'<line x1="{x}" y1="{top - 18}" x2="{x}" y2="{height - 70}" stroke="#dbe4f0" stroke-width="1"/>')
        parts.append(svg_text(x, top - 28, f"{tick}%", size=12, weight="700", fill="#64748b", anchor="middle", family=FONT_STACK))

    for idx, row in enumerate(rows):
        y = top + idx * row_height
        tier = tier_name(row["pass_rate"])
        color = tier_color(tier)
        fill, text = basis_colors(row["kind"])
        bar_w = chart_width * row["pass_rate"] / 100.0
        parts.append(svg_text(66, y + 24, row["language"], size=18, weight="700", family=FONT_STACK))
        pill_w = 70 if row["basis_tag"] == "FULL" else 104
        parts.append(svg_rect(200, y + 6, pill_w, 22, fill, radius=11))
        parts.append(svg_text(200 + pill_w / 2, y + 22, row["basis_tag"], size=11, weight="800", fill=text, anchor="middle", family=FONT_STACK))
        parts.append(svg_text(285, y + 23, row["basis_detail"], size=13, fill="#64748b"))
        parts.append(svg_rect(chart_left, y, chart_width, 24, "#e2e8f0", radius=12))
        parts.append(svg_rect(chart_left, y, bar_w, 24, f"url(#{tier.lower()}grad)", radius=12))
        parts.append(svg_text(chart_left + chart_width + 18, y + 20, f'{row["pass_rate"]:.1f}%', size=17, weight="800", fill=color, family=FONT_STACK))

    parts.append(svg_text(66, height - 34, "Added languages remain in the same ranking, but their tags indicate whether they come from validated or legacy translated slices.", size=17, fill="#475569"))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_acb_full_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def render_extension_chart(summary: dict) -> None:
    ext = summary["extension_slices"]
    rows = [
        ("typescript_effect", ext["typescript_effect"]["pass_rate"], "SLICE", f'{ext["typescript_effect"]["passed"]}/{ext["typescript_effect"]["source_rows"]}', "#7c3aed"),
        ("lean4", ext["lean4"]["pass_rate_on_validated_rows"], "VALIDATED", f'{ext["lean4"]["passed"]}/{ext["lean4"]["validated_rows"]}', "#b45309"),
        ("gleam", ext["gleam"]["pass_rate_on_validated_rows"], "VALIDATED", f'{ext["gleam"]["passed"]}/{ext["gleam"]["validated_rows"]}', "#b45309"),
    ]
    width = 1080
    height = 500
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.extend(svg_defs())
    add_background(parts, width, height)
    parts.append(svg_rect(24, 24, width - 48, height - 48, "url(#cardgrad)", radius=32, stroke="#dbe4f0"))
    parts.append(svg_text(52, 86, "Added language tracks", size=28, weight="800", family=FONT_STACK))
    parts.append(svg_text(52, 124, "Kept as a compact reference card even though the README now uses the unified leaderboard.", size=17, fill="#475569"))
    for idx, (language, rate, tag, detail, color) in enumerate(rows):
        y = 186 + idx * 92
        parts.append(svg_rect(52, y, 976, 64, "#ffffff", radius=24, stroke="#e2e8f0"))
        fill, text = basis_colors("validated" if tag == "VALIDATED" else "slice")
        parts.append(svg_text(80, y + 39, language, size=22, weight="700", family=FONT_STACK))
        parts.append(svg_rect(240, y + 20, 104 if tag == "VALIDATED" else 70, 24, fill, radius=12))
        parts.append(svg_text(292 if tag == "VALIDATED" else 275, y + 37, tag, size=11, weight="800", fill=text, anchor="middle", family=FONT_STACK))
        parts.append(svg_text(360, y + 38, detail, size=15, fill="#64748b"))
        parts.append(svg_rect(510, y + 20, 360, 24, "#e2e8f0", radius=12))
        parts.append(svg_rect(510, y + 20, 360 * rate / 60.0, 24, color, radius=12))
        parts.append(svg_text(900, y + 38, f"{rate:.1f}%", size=20, weight="800", fill=color, family=FONT_STACK))
    parts.append("</svg>")
    (FIGURES_DIR / "fork_extension_languages_gpt_5_4_medium.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    ensure_dirs()
    summary = load_summary()
    export_yaml(summary)
    render_overview(summary)
    render_language_guide(summary)
    render_share_card(summary)
    render_all_language_bars(summary)
    render_extension_chart(summary)
    print("Wrote results/summary.yaml")
    print("Wrote results/main_benchmark.yaml")
    print("Wrote results/extension_slices.yaml")
    print("Wrote results/all_languages.yaml")
    print("Wrote results/model_guidance.yaml")
    print("Wrote figures/fork_results_overview_gpt_5_4_medium.svg")
    print("Wrote figures/fork_model_language_guide.svg")
    print("Wrote figures/fork_leaderboard_share_gpt_5_4_medium.svg")
    print("Wrote figures/fork_acb_full_gpt_5_4_medium.svg")
    print("Wrote figures/fork_extension_languages_gpt_5_4_medium.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
