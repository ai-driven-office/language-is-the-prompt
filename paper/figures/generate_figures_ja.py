#!/usr/bin/env python3
"""日本語版の論文図表を生成するスクリプト。

generate_figures.py の日本語版。
タイトル・軸ラベル・アノテーション・凡例をすべて日本語に翻訳。
言語名 (Elixir, Python 等) と技術用語 (Pass@1 等) は英語のまま。
出力ファイル名は _ja サフィックス付き。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "figures"

# ── Refined colour palette ──────────────────────────────────────────────
COLORS: Dict[str, str] = {
    "elixir":     "#6B4FA2",   # Deep purple -- hero colour
    "elixir_lt":  "#A992D4",   # Light purple for fills
    "python":     "#D48B00",   # Warm amber
    "typescript": "#2A9D8F",   # Teal
    "kotlin":     "#4C78A8",   # Steel blue
    "csharp":     "#2A9D8F",   # Teal (same family as TS)
    "javascript": "#C44E52",   # Muted red
    "go":         "#00ADD8",   # Go blue
    "neutral":    "#B7BDC6",   # Soft grey for non-highlighted
    "neutral_dk": "#8B95A1",   # Darker neutral
    "dark":       "#2D3748",   # Near-black for text/axes
    "contracts":  "#38A89D",   # Strong teal for contract effects
    "examples":   "#E6B422",   # Gold for examples
    "grid":       "#E5E7EB",   # Very light grid
    "text":       "#1A202C",   # Rich black
    "bg":         "#FAFAF9",   # Warm off-white
    "accent":     "#E53E3E",   # Red accent for annotations
    "positive":   "#38A169",   # Green for positive
    "negative":   "#E53E3E",   # Red for negative
}

# ── Global rcParams (Japanese font) ───────────────────────────────────
plt.rcParams.update({
    "font.family":        "Hiragino Sans",
    "font.size":          11,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.labelsize":     11,
    "axes.labelweight":   "medium",
    "xtick.labelsize":    10,
    "ytick.labelsize":    10,
    "figure.dpi":         300,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.15,
    "pdf.fonttype":       42,
    "ps.fonttype":        42,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.facecolor":     COLORS["bg"],
    "figure.facecolor":   "white",
    "axes.edgecolor":     "#CBD5E0",
    "xtick.color":        COLORS["dark"],
    "ytick.color":        COLORS["dark"],
    "axes.labelcolor":    COLORS["dark"],
    "axes.titlecolor":    COLORS["text"],
    "legend.framealpha":  0.0,
    "legend.fontsize":    10,
})


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="pdf")
    png_name = name.replace(".pdf", ".png")
    fig.savefig(OUT / png_name, format="png")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────
# 図1 : 20言語リーダーボード
# ─────────────────────────────────────────────────────────────────────────
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
        elif lang == "Go":
            bar_colors.append(COLORS["go"])
        else:
            bar_colors.append(COLORS["neutral"])

    fig, ax = plt.subplots(figsize=(9.0, 7.6))
    ax2 = ax.twiny()

    bars = ax.barh(y, pass1, color=bar_colors, edgecolor="none", height=0.78,
                   zorder=3, alpha=0.92)
    ax2.scatter(hard, y, s=26, color=COLORS["dark"], alpha=0.80, zorder=5,
                marker="D", linewidths=0.4, edgecolors="white")

    for yi, val in zip(y, pass1):
        weight = "bold" if val > 70 else "normal"
        ax.text(val + 0.9, yi, f"{val:.1f}", va="center", ha="left",
                fontsize=9.5, color=COLORS["text"], fontweight=weight)

    ax.set_yticks(y)
    ax.set_yticklabels(languages, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 95)
    ax2.set_xlim(0, 82)
    ax.set_xlabel("合格率 Pass@1 (%)", fontweight="medium")
    ax2.set_xlabel("難問タスク比率 (%)", fontweight="medium", color=COLORS["neutral_dk"])
    ax.set_title("AutoCodeBench リーダーボード（GPT-5.4 による再現、2026年3月11日時点）",
                 pad=18, fontsize=12)

    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)
    ax2.grid(False)
    ax2.tick_params(colors=COLORS["neutral_dk"])

    # Highlight the gap
    ax.axhline(y=0.5, xmin=0, xmax=pass1[0] / 95, color=COLORS["elixir"],
               linewidth=0, alpha=0)  # placeholder for spacing

    legend_items = [
        Line2D([0], [0], color=COLORS["elixir"], lw=8, label="Elixir", alpha=0.92),
        Line2D([0], [0], color=COLORS["python"], lw=8, label="Python", alpha=0.92),
        Line2D([0], [0], color=COLORS["typescript"], lw=8, label="TypeScript", alpha=0.92),
        Line2D([0], [0], color=COLORS["go"], lw=8, label="Go", alpha=0.92),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=COLORS["dark"],
               markersize=6, label="難問タスク比率", alpha=0.8),
    ]
    ax.legend(handles=legend_items, frameon=False, loc="lower right",
              borderpad=1, handletextpad=0.8)
    fig.tight_layout()
    save(fig, "figure_1_leaderboard_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図2 : 言語設計空間マップ
# ─────────────────────────────────────────────────────────────────────────
def fig_design_space() -> None:
    rows = read_csv(DATA / "leaderboard.csv")

    x = [float(r["cf_score"]) for r in rows]
    y = [-float(r["mutability"]) for r in rows]
    docs = [float(r["docs"]) for r in rows]
    pass1 = [float(r["pass1"]) for r in rows]
    langs = [r["language"] for r in rows]
    sizes = [d * 28 for d in docs]

    fig, ax = plt.subplots(figsize=(7.6, 6.0))
    sc = ax.scatter(x, y, s=sizes, c=pass1, cmap="viridis", alpha=0.88,
                    edgecolors="white", linewidths=0.6, zorder=3)
    ax.set_title("言語設計空間マップ\nElixir のみが右上の外れ値に位置する",
                 pad=12, fontsize=12)
    ax.set_xlabel("制御フロー明示性スコア（高いほど明示的）")
    ax.set_ylabel("状態明瞭度 = −可変性負荷（高いほどクリーン）")
    ax.grid(color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)

    # Annotate key languages with offset arrows
    annotate_config = {
        "Elixir":     (1.0, 1.5, "bold"),
        "Racket":     (0.6, 1.5, "normal"),
        "Python":     (0.5, -2.0, "bold"),
        "Kotlin":     (0.8, 2.0, "normal"),
        "TypeScript": (0.8, -2.5, "bold"),
        "Go":         (0.6, -2.0, "bold"),
        "C#":         (0.6, 2.0, "normal"),
        "Rust":       (0.5, 2.0, "normal"),
        "Scala":      (0.5, 2.0, "normal"),
    }
    for lang, (dx, dy, weight) in annotate_config.items():
        idx = langs.index(lang)
        fontsize = 10.5 if weight == "bold" else 9
        color = COLORS["elixir"] if lang == "Elixir" else COLORS["text"]
        ax.annotate(lang, (x[idx], y[idx]),
                    xytext=(x[idx] + dx, y[idx] + dy),
                    fontsize=fontsize, fontweight=weight, color=color,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="#9CA3AF"),
                    zorder=6)

    ax.text(3.0, -33.5, "バブルサイズ＝ドキュメント充実度", fontsize=9,
            color=COLORS["neutral_dk"], fontstyle="italic")
    cbar = fig.colorbar(sc, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label("合格率 Pass@1 (%)", fontsize=10)
    cbar.ax.tick_params(labelsize=9)
    fig.tight_layout()
    save(fig, "figure_2_design_space_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図3 : 難易度耐性
# ─────────────────────────────────────────────────────────────────────────
def fig_difficulty_resilience() -> None:
    rows = read_csv(DATA / "difficulty_buckets.csv")
    stages = ["易", "中", "難"]
    xvals = [0, 1, 2]

    style = {
        "Elixir":     (COLORS["elixir"],     "o",  2.8),
        "Kotlin":     (COLORS["kotlin"],      "^",  1.8),
        "C#":         (COLORS["csharp"],      "D",  1.8),
        "Python":     (COLORS["python"],      "s",  2.4),
        "JavaScript": (COLORS["javascript"],  "v",  1.8),
    }

    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    for row in rows:
        lang = row["language"]
        vals = [float(row["easy"]), float(row["medium"]), float(row["hard"])]
        color, marker, lw = style[lang]
        zorder = 5 if lang in ("Elixir", "Python") else 3
        ax.plot(xvals, vals, marker=marker, markersize=8, linewidth=lw,
                color=color, label=lang, zorder=zorder, alpha=0.92)

    ax.set_xticks(xvals)
    ax.set_xticklabels(stages, fontsize=11)
    ax.set_ylim(18, 105)
    ax.set_ylabel("合格率 Pass@1 (%)")
    ax.set_title("難易度耐性：Elixir はタスクが難しくなっても性能がほとんど低下しない",
                 pad=12, fontsize=12)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8)

    # Drop annotations with styled arrows
    ax.annotate(
        "Elixir：わずか −10.3 pp",
        xy=(2, 86.3), xytext=(1.05, 96),
        arrowprops=dict(arrowstyle="->", lw=1.3, color=COLORS["elixir"],
                        connectionstyle="arc3,rad=-0.15"),
        color=COLORS["elixir"], fontsize=10.5, fontweight="bold",
    )
    ax.annotate(
        "Python：−50.4 pp",
        xy=(2, 31.6), xytext=(0.95, 42),
        arrowprops=dict(arrowstyle="->", lw=1.3, color=COLORS["python"],
                        connectionstyle="arc3,rad=0.15"),
        color=COLORS["python"], fontsize=10.5, fontweight="bold",
    )

    # Shade the gap on hard tasks
    ax.fill_between([1.85, 2.15], [31.6, 31.6], [86.3, 86.3],
                    alpha=0.06, color=COLORS["elixir"], zorder=0)

    ax.legend(frameon=False, ncol=3, loc="lower left", fontsize=10)
    fig.tight_layout()
    save(fig, "figure_3_difficulty_resilience_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図4 : スイートA アブレーション
# ─────────────────────────────────────────────────────────────────────────
def fig_suite_a() -> None:
    rows = read_csv(DATA / "suite_a.csv")
    labels = [r["label"] for r in rows]
    vals = [float(r["pass1"]) for r in rows]
    deltas = [float(r["delta"]) for r in rows]
    x = list(range(len(rows)))
    colors = [COLORS["elixir"], COLORS["elixir_lt"], COLORS["neutral"], COLORS["neutral_dk"]]

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    bars = ax.bar(x, vals, color=colors, edgecolor="none", width=0.68, zorder=3)

    # Python baseline reference line
    ax.axhline(43.9, color=COLORS["python"], linestyle="--", linewidth=1.4,
               alpha=0.85, zorder=2)
    ax.text(0.85, 45.5, "Python ACB ベースライン (43.9%)", color=COLORS["python"],
            fontsize=9, ha="left", va="bottom", fontstyle="italic")

    for idx, (bar, val, delta) in enumerate(zip(bars, vals, deltas)):
        if idx == 0:
            text = f"{val:.1f}%"
        elif idx == 1:
            text = f"{val:.1f}%\n（変化なし）"
        else:
            text = f"{val:.1f}%\n({delta:+.1f} pp)"
        weight = "bold" if idx <= 1 else "normal"
        color = COLORS["text"] if idx <= 1 else COLORS["accent"]
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.8, text,
                ha="center", va="bottom", fontsize=10, color=color,
                fontweight=weight)

    # Draw a bracket showing the drop
    ax.annotate("", xy=(2, 46.0), xytext=(0, 84.3),
                arrowprops=dict(arrowstyle="<->", lw=1.2,
                                color=COLORS["accent"], ls="--"))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_ylabel("合格率 Pass@1 (%)")
    ax.set_title("スイートA：ドキュメント構造が支配的な因果シグナルである",
                 pad=12, fontsize=12)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)
    fig.tight_layout()
    save(fig, "figure_4_suite_a_ablation_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図5 : 要因分析（2パネル）
# ─────────────────────────────────────────────────────────────────────────
def fig_factorial_effects() -> None:
    left_rows = read_csv(DATA / "factorial_main_effects.csv")
    right_rows = read_csv(DATA / "contract_effect_by_language.csv")

    order = ["state_guidance", "docs_rich", "examples", "contracts_explicit"]
    left_sorted = [next(r for r in left_rows if r["factor"] == name) for name in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.4),
                                    gridspec_kw={"width_ratios": [1.3, 0.9]})

    # Japanese labels for factor names
    factor_labels_ja = {
        "state_guidance": "状態ガイダンス",
        "docs_rich": "リッチドキュメント",
        "examples": "実行可能サンプル",
        "contracts_explicit": "明示的契約",
    }
    left_labels = [factor_labels_ja.get(r["factor"], r["label"].replace("_", " ").title())
                   for r in left_sorted]
    left_vals = [float(r["effect"]) for r in left_sorted]
    left_colors = [COLORS["contracts"] if r["factor"] == "contracts_explicit"
                   else (COLORS["examples"] if r["factor"] == "examples"
                   else COLORS["neutral"]) for r in left_sorted]
    yy = list(range(len(left_sorted)))
    ax1.barh(yy, left_vals, color=left_colors, edgecolor="none", height=0.58,
             zorder=3, alpha=0.90)
    ax1.axvline(0, color=COLORS["dark"], linewidth=1.0, zorder=2)
    ax1.set_yticks(yy)
    ax1.set_yticklabels(left_labels)
    ax1.set_xlabel("合格率スケール上のマッチド効果")
    ax1.set_title("主効果（384行要因計画）", fontsize=12, pad=10)
    ax1.grid(axis="x", color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)

    for yi, row in zip(yy, left_sorted):
        val = float(row["effect"])
        sig = row["significant"] == "1"
        marker = "  **" if sig else ""
        # Place tiny negative values to the right of zero to avoid y-label overlap
        if val < 0 and abs(val) < 0.05:
            x_text = 0.015
            ha = "left"
        elif val >= 0:
            x_text = val + 0.015
            ha = "left"
        else:
            x_text = val - 0.015
            ha = "right"
        weight = "bold" if sig else "normal"
        ax1.text(x_text, yi, f"{val:+.3f}{marker}", va="center", ha=ha,
                 fontsize=10, color=COLORS["text"], fontweight=weight)

    right_labels = [r["language"] for r in right_rows]
    right_vals = [float(r["effect"]) for r in right_rows]
    lang_colors = {"Elixir": COLORS["elixir"], "Python": COLORS["python"],
                   "TypeScript": COLORS["typescript"]}
    right_colors = [lang_colors.get(r["language"], COLORS["neutral"]) for r in right_rows]
    xx = list(range(len(right_rows)))
    bars = ax2.bar(xx, right_vals, color=right_colors, edgecolor="none",
                   width=0.58, zorder=3, alpha=0.90)
    ax2.set_xticks(xx)
    ax2.set_xticklabels(right_labels, fontsize=10)
    ax2.set_ylim(0, 0.56)
    ax2.set_ylabel("契約効果 ($\\Delta$)")
    ax2.set_title("言語別の契約効果", fontsize=12, pad=10)
    ax2.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)

    for bar, row in zip(bars, right_rows):
        val = float(row["effect"])
        sig = row["significant"] == "1"
        marker = "  **" if sig else ""
        weight = "bold" if sig else "normal"
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.015,
                 f"{val:+.3f}{marker}", ha="center", va="bottom",
                 fontsize=10, fontweight=weight)

    fig.suptitle("明示的契約は Holm 補正後も唯一有効なポータブル介入である",
                 fontsize=11.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "figure_5_factorial_effects_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図6 : Elixir ドキュメントパイプライン
# ─────────────────────────────────────────────────────────────────────────
def fig_docs_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(10.6, 3.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.96,
            "Elixir のドキュメントアーキテクチャ：単一の可読性スタック",
            ha="center", va="top", fontsize=13, color=COLORS["text"],
            fontweight="bold")

    boxes = [
        (0.02, 0.32, 0.21, 0.46, "#E8E3F3", "#6B4FA2",
         "ソースコード\n\n@moduledoc\n@doc, @spec"),
        (0.265, 0.32, 0.21, 0.46, "#D6EAF0", "#2B6CB0",
         "実行可能サンプル\n\nExUnit.DocTest\nドキュメントを検証可能に"),
        (0.51, 0.32, 0.21, 0.46, "#D5F0EB", "#276749",
         "標準生成\n\nExDoc が統一\nHTML/EPUB を出力"),
        (0.755, 0.32, 0.21, 0.46, "#FDF0DB", "#975A16",
         "エコシステム配信\n\nHexDocs + ランタイム\nCode.fetch_docs/1"),
    ]

    for x0, y0, w, h, bgcolor, bordercolor, text in boxes:
        patch = FancyBboxPatch(
            (x0, y0), w, h,
            boxstyle="round,pad=0.015,rounding_size=0.022",
            linewidth=1.6, edgecolor=bordercolor, facecolor=bgcolor,
        )
        ax.add_patch(patch)
        ax.text(x0 + w / 2, y0 + h / 2, text, ha="center", va="center",
                fontsize=10, color=COLORS["dark"], linespacing=1.35)

    for x1, x2 in [(0.23, 0.265), (0.475, 0.51), (0.72, 0.755)]:
        arrow = FancyArrowPatch(
            (x1, 0.55), (x2, 0.55),
            arrowstyle="-|>", mutation_scale=14, linewidth=1.8,
            color=COLORS["dark"], alpha=0.7,
        )
        ax.add_patch(arrow)

    ax.text(0.5, 0.12,
            "要点：目的、契約、サンプル、公開、検索が\n"
            "単一のパイプラインに集約されている点がアーキテクチャ上の鍵である。",
            ha="center", va="center", fontsize=10.5, color=COLORS["dark"],
            fontstyle="italic")
    ax.text(0.5, 0.02,
            "Python と TypeScript もリッチなドキュメントを支援するが、"
            "規約が緩く、ツールチェーンがより断片化している。",
            ha="center", va="center", fontsize=9, color=COLORS["neutral_dk"])

    fig.tight_layout()
    save(fig, "figure_6_docs_pipeline_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
# 図A1 : ロバストネスチェック
# ─────────────────────────────────────────────────────────────────────────
def fig_robustness() -> None:
    rows = read_csv(DATA / "robustness.csv")
    labels = [r["label"] for r in rows]
    lows = [float(r["low"]) for r in rows]
    highs = [float(r["high"]) for r in rows]
    centers = [float(r["center"]) for r in rows]
    colors = [COLORS["contracts"] if r["group"] == "Contracts"
              else COLORS["examples"] for r in rows]
    y = list(range(len(rows)))[::-1]

    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    for yi, low, high, center, color in zip(y, lows, highs, centers, colors):
        ax.plot([low, high], [yi, yi], color=color, linewidth=5.5,
                solid_capstyle="round", alpha=0.70, zorder=3)
        ax.scatter([center], [yi], color=COLORS["dark"], s=35, zorder=5,
                   edgecolors="white", linewidths=0.8)

    ax.axvline(0, color=COLORS["dark"], linewidth=1.0, linestyle="--",
               alpha=0.5, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("合格率スケール上の効果範囲")
    ax.set_title("ロバストネスチェック：契約効果は一貫して正の値を示す",
                 pad=12, fontsize=12)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6, alpha=0.8, zorder=0)
    ax.set_xlim(-0.12, 0.58)

    # Legend
    legend_items = [
        Line2D([0], [0], color=COLORS["contracts"], lw=5, label="契約効果",
               alpha=0.7),
        Line2D([0], [0], color=COLORS["examples"], lw=5, label="サンプル効果",
               alpha=0.7),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["dark"],
               markersize=6, label="点推定"),
    ]
    ax.legend(handles=legend_items, frameon=False, loc="lower right")
    fig.tight_layout()
    save(fig, "figure_A1_robustness_ja.pdf")


# ─────────────────────────────────────────────────────────────────────────
def main() -> None:
    fig_leaderboard()
    fig_design_space()
    fig_difficulty_resilience()
    fig_suite_a()
    fig_factorial_effects()
    fig_docs_pipeline()
    fig_robustness()
    print("[OK] 日本語版の図表 PDF + PNG を出力しました →", OUT)


if __name__ == "__main__":
    main()
