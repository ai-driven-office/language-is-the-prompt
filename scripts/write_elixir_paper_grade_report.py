#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_RESULTS_DIR = REPO_ROOT / "results" / "elixir_active_suites"
BASE_RESULTS_DIR = REPO_ROOT / "results"
DATA_DIR = REPO_ROOT / "data" / "elixir_active_suites"

ACTIVE_SUITES = [
    ("suite_a", "Documentation Quality", "full_docs"),
    ("suite_d", "Pattern Matching and Control Flow", "baseline"),
    ("suite_e", "Result Contracts", "baseline"),
    ("suite_f", "Mutability and State Style", "baseline"),
]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_csv_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return read_csv(path)


def to_map(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows}


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def render_suite_section(lines: list[str], suite_id: str, title: str, baseline: str) -> None:
    summary_rows = read_csv_if_exists(ACTIVE_RESULTS_DIR / f"{suite_id}_summary.csv")
    if not summary_rows:
        return
    pair_map = to_map(read_csv_if_exists(ACTIVE_RESULTS_DIR / f"{suite_id}_paired_stats.csv"), "condition")
    summary_map = to_map(summary_rows, "condition")
    missing_rows = read_csv_if_exists(ACTIVE_RESULTS_DIR / f"{suite_id}_missing_generations.csv")
    lines.extend(
        [
            f"## {title}",
            "",
            "| Condition | Pass Rate | 95% CI | Delta vs Baseline | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary_rows:
        condition = row["condition"]
        if condition == baseline:
            lines.append(
                f"| {condition} | {row['pass_rate']}% | {row['ci_low']}% to {row['ci_high']}% | +0.0 | 0 | 0 | 1.0 | 0.0 to 0.0 | 100.0% |"
            )
            continue
        pair = pair_map.get(condition, {})
        lines.append(
            f"| {condition} | {row['pass_rate']}% | {row['ci_low']}% to {row['ci_high']}% | "
            f"{row['delta_vs_baseline']} | {pair.get('baseline_only_wins', '')} | {pair.get('condition_only_wins', '')} | "
            f"{pair.get('mcnemar_pvalue', '')} | {pair.get('delta_ci_low', '')} to {pair.get('delta_ci_high', '')} | "
            f"{pair.get('condition_pass_rate_on_baseline_pass_subset', '')}% |"
        )
    lines.append("")
    if missing_rows:
        lines.extend(
            [
                f"- Missing generations counted as failures: `{len(missing_rows)}`",
                "",
            ]
        )
    if suite_id == "suite_a":
        lines.extend(
            [
                "Read:",
                "",
                "- This suite directly tests whether documentation richness is carrying Elixir.",
                "- The strongest negative intervention is the one that collapses the prompt down to signatures only.",
            ]
        )
    elif suite_id == "suite_d":
        lines.extend(
            [
                "Read:",
                "",
                "- This suite tests whether forcing alternative control-flow surface forms changes outcomes materially.",
                "- A flat result here argues against a simple 'pattern matching alone explains everything' story.",
            ]
        )
    elif suite_id == "suite_e":
        lines.extend(
            [
                "Read:",
                "",
                "- This suite tests whether explicit tagged-contract prompting helps relative to weaker implicit sentinel contracts.",
                "- If tagged-tuple prompting stays competitive while sentinel prompting degrades, that strengthens the explicit-contract hypothesis.",
            ]
        )
    elif suite_id == "suite_f":
        lines.extend(
            [
                "Read:",
                "",
                "- This suite tests whether forcing more explicit or more stepwise state style moves the needle materially.",
                "- A flat result argues that low mutability burden may matter more as a language property than as a prompt-level style intervention.",
            ]
        )
    lines.append("")


def main() -> None:
    suite_h = to_map(
        read_csv(BASE_RESULTS_DIR / "elixir_suite_h" / "suite_h_artifact_controls.csv"),
        "language",
    )["elixir"]
    suite_a_task_count = count_lines(DATA_DIR / "suite_a.jsonl") // 4
    suite_e_task_count = count_lines(DATA_DIR / "suite_e.jsonl") // 3

    lines = [
        "# Elixir Paper-Grade Active Study",
        "",
        "## Executive summary",
        "",
        "- We replicated Elixir's strong benchmark result in the corrected local run: `87.4%` pass@1.",
        "- That lead survives benchmark-artifact controls: `+40.4` points vs the difficulty-only expectation and `+42.7` points vs the difficulty+question-length expectation.",
        "- The strongest current causal evidence points to documentation richness and explicit public contracts.",
        "- Pattern matching and low hidden-state burden remain plausible secondary contributors, not yet the primary proved causes.",
        "",
        "## Method",
        "",
        "- Model: `gpt-5.4` with medium reasoning",
        "- Language under study: `elixir`",
        f"- Active documentation task count: `{suite_a_task_count}` source tasks",
        f"- Active contract task count: `{suite_e_task_count}` source tasks",
        "- Scoring: native Elixir execution through the corrected local scorer",
        "- Analysis: paired condition comparisons against the same task set",
        "",
        "## Benchmark replication evidence",
        "",
        f"- Corrected Elixir pass rate: `{suite_h['observed_pass_rate']}%`",
        f"- Expected pass rate under difficulty-only control: `{suite_h['expected_pass_rate_difficulty_only']}%`",
        f"- Expected pass rate under difficulty+question-length control: `{suite_h['expected_pass_rate_difficulty_and_question_len']}%`",
        f"- Delta vs difficulty-only expectation: `{suite_h['delta_vs_difficulty_only']}` points",
        f"- Delta vs difficulty+question-length expectation: `{suite_h['delta_vs_difficulty_and_question_len']}` points",
        f"- Delta vs difficulty+full-test-length expectation: `{suite_h['delta_vs_difficulty_and_full_test_len']}` points",
        "",
    ]

    for suite_id, title, baseline in ACTIVE_SUITES:
        render_suite_section(lines, suite_id, title, baseline)

    lines.extend(
        [
            "## Claim boundary",
            "",
            "- These active suites can show which interventions materially change outcomes on matched Elixir tasks.",
            "- They cannot by themselves prove what the entire public Elixir corpus taught the model during pretraining.",
            "- The strongest defensible statement today is that explicit docs and explicit contracts are the best-supported explanations for Elixir's benchmark advantage in this setup.",
            "",
            "## What other language designers should copy",
            "",
            "- Normalize result-shape conventions instead of encouraging ad hoc sentinel returns.",
            "- Make reference docs concrete enough that the API contract remains legible under compression.",
            "- Keep docs, tests, and public behavior tightly aligned.",
            "- Reduce opportunities for hidden mutable state and ambiguous control flow.",
        ]
    )

    (ACTIVE_RESULTS_DIR / "paper_grade_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
