#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import defaultdict
from math import comb, sqrt
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCORED_PATH = REPO_ROOT / "outputs" / "explicit_task_panel" / "gpt-5-4-medium.exec.jsonl"
RESULTS_DIR = REPO_ROOT / "results" / "explicit_task_panel"

Z_95 = 1.96


def load_rows() -> list[dict]:
    rows: list[dict] = []
    with SCORED_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                original = row["original_data"]
                rows.append(
                    {
                        "experiment_id": original["experiment_id"],
                        "task_id": original["task_id"],
                        "language": original["language"],
                        "condition_id": original["condition_id"],
                        "title": original["title"],
                        "success": int(bool(row["success"])),
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def percent(passed: int, total: int) -> float:
    return 0.0 if total == 0 else round(100.0 * passed / total, 1)


def wilson_interval(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    margin = z * sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return round(low * 100.0, 1), round(high * 100.0, 1)


def exact_sign_p_value(wins: int, losses: int) -> float:
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    tail = min(wins, losses)
    probability = sum(comb(discordant, k) for k in range(0, tail + 1)) / (2**discordant)
    return min(1.0, round(2.0 * probability, 6))


def overall_rows(rows: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        by_key[(row["language"], row["condition_id"])].append(row["success"])
    out: list[dict] = []
    for (language, condition_id), values in sorted(by_key.items()):
        passed = sum(values)
        total = len(values)
        ci_low, ci_high = wilson_interval(passed, total)
        out.append(
            {
                "language": language,
                "condition_id": condition_id,
                "passed": passed,
                "total": total,
                "pass_rate": percent(passed, total),
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )
    return out


def aggregate_condition_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        grouped[row["condition_id"]].append(row["success"])
    out: list[dict] = []
    for condition_id, values in sorted(grouped.items()):
        passed = sum(values)
        total = len(values)
        ci_low, ci_high = wilson_interval(passed, total)
        out.append(
            {
                "condition_id": condition_id,
                "passed": passed,
                "total": total,
                "pass_rate": percent(passed, total),
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )
    return out


def task_fixed_rows(rows: list[dict]) -> list[dict]:
    grid: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for row in rows:
        grid[(row["language"], row["task_id"])][row["condition_id"]] = row["success"]

    comparisons = [
        ("rich_contract", "baseline_compact"),
        ("rich_contract_examples", "baseline_compact"),
        ("rich_contract_examples", "rich_contract"),
    ]

    by_language: dict[str, list[dict]] = defaultdict(list)
    for (language, _task_id), row_map in grid.items():
        by_language[language].append(row_map)

    out: list[dict] = []
    for language, task_maps in sorted(by_language.items()):
        for left, right in comparisons:
            left_only = 0
            right_only = 0
            tied_pass = 0
            tied_fail = 0
            deltas: list[int] = []
            for task_map in task_maps:
                a = task_map.get(left, 0)
                b = task_map.get(right, 0)
                deltas.append(a - b)
                if a == 1 and b == 0:
                    left_only += 1
                elif a == 0 and b == 1:
                    right_only += 1
                elif a == 1 and b == 1:
                    tied_pass += 1
                else:
                    tied_fail += 1
            out.append(
                {
                    "language": language,
                    "comparison": f"{left}_vs_{right}",
                    "mean_task_delta": round(sum(deltas) / len(deltas), 3) if deltas else 0.0,
                    "left_only_wins": left_only,
                    "right_only_wins": right_only,
                    "tied_pass": tied_pass,
                    "tied_fail": tied_fail,
                    "task_count": len(task_maps),
                    "discordant_n": left_only + right_only,
                    "sign_test_p": exact_sign_p_value(left_only, right_only),
                }
            )
    return out


def aggregate_paired_rows(rows: list[dict]) -> list[dict]:
    grid: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for row in rows:
        grid[(row["language"], row["task_id"])][row["condition_id"]] = row["success"]

    comparisons = [
        ("rich_contract", "baseline_compact"),
        ("rich_contract_examples", "baseline_compact"),
        ("rich_contract_examples", "rich_contract"),
    ]
    out: list[dict] = []
    for left, right in comparisons:
        left_only = 0
        right_only = 0
        tied_pass = 0
        tied_fail = 0
        deltas: list[int] = []
        for task_map in grid.values():
            a = task_map.get(left, 0)
            b = task_map.get(right, 0)
            deltas.append(a - b)
            if a == 1 and b == 0:
                left_only += 1
            elif a == 0 and b == 1:
                right_only += 1
            elif a == 1 and b == 1:
                tied_pass += 1
            else:
                tied_fail += 1
        out.append(
            {
                "scope": "all_languages",
                "comparison": f"{left}_vs_{right}",
                "mean_task_delta": round(sum(deltas) / len(deltas), 3) if deltas else 0.0,
                "left_only_wins": left_only,
                "right_only_wins": right_only,
                "tied_pass": tied_pass,
                "tied_fail": tied_fail,
                "pair_count": len(grid),
                "discordant_n": left_only + right_only,
                "sign_test_p": exact_sign_p_value(left_only, right_only),
            }
        )
    return out


def by_task_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        grouped[(row["task_id"], row["title"], row["condition_id"])].append(row["success"])
    out: list[dict] = []
    for (task_id, title, condition_id), values in sorted(grouped.items()):
        passed = sum(values)
        total = len(values)
        ci_low, ci_high = wilson_interval(passed, total)
        out.append(
            {
                "task_id": task_id,
                "title": title,
                "condition_id": condition_id,
                "passed": passed,
                "total": total,
                "pass_rate": percent(passed, total),
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )
    return out


def task_language_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (row["task_id"], row["language"], row["condition_id"]),
    )


def find_row(rows: list[dict], **filters: str) -> dict:
    for row in rows:
        if all(str(row.get(key)) == str(value) for key, value in filters.items()):
            return row
    raise KeyError(f"Could not find row with filters={filters!r}")


def claims_rows(overall: list[dict], paired: list[dict]) -> list[dict]:
    elixir_overall = sum(row["passed"] for row in overall if row["language"] == "elixir")
    python_overall = sum(row["passed"] for row in overall if row["language"] == "python")
    typescript_overall = sum(row["passed"] for row in overall if row["language"] == "typescript")
    per_language_total = sum(row["total"] for row in overall if row["language"] == "elixir")
    examples_vs_baseline = find_row(
        paired,
        scope="all_languages",
        comparison="rich_contract_examples_vs_baseline_compact",
    )

    return [
        {
            "claim": "Elixir's ACB leaderboard advantage is real after artifact controls.",
            "evidence": "ACB-Full reproduction + Suite H artifact controls",
            "estimator": "Observed minus difficulty/length-adjusted expectation",
            "effect": "+42.7 points versus difficulty+question-length expected rate",
            "significance_or_status": "Large and stable across all artifact controls",
            "verdict": "strong",
        },
        {
            "claim": "Within Elixir, documentation structure materially drives performance.",
            "evidence": "Suite A paper-grade active ablation",
            "estimator": "Paired delta versus full_docs",
            "effect": "minimal_docs -38.4 points; signature_only -41.4 points",
            "significance_or_status": "Holm-adjusted p < 1e-15",
            "verdict": "strong",
        },
        {
            "claim": "Examples alone explain Elixir's advantage.",
            "evidence": "Suite A paper-grade active ablation",
            "estimator": "reference_no_examples versus full_docs",
            "effect": "0.0 point delta",
            "significance_or_status": "No effect",
            "verdict": "not_established",
        },
        {
            "claim": "Concrete examples directionally help the matched panel, but not cleanly for every language.",
            "evidence": "Explicit-task panel (48 matched language-task pairs)",
            "estimator": "Paired sign test for rich_contract_examples versus baseline_compact",
            "effect": (
                f"{examples_vs_baseline['left_only_wins']} improvements, "
                f"{examples_vs_baseline['right_only_wins']} degradations, "
                f"mean delta +{examples_vs_baseline['mean_task_delta']}"
            ),
            "significance_or_status": (
                f"Exact two-sided sign p = {examples_vs_baseline['sign_test_p']}; "
                "low-power directional result"
            ),
            "verdict": "directional",
        },
        {
            "claim": "Elixir universally dominates once tasks are tightly matched.",
            "evidence": "Explicit-task cross-language panel",
            "estimator": "Per-language pass rate on the 144-row panel",
            "effect": (
                f"Elixir {round(100.0 * elixir_overall / per_language_total, 1)}%, "
                f"Python {round(100.0 * python_overall / per_language_total, 1)}%, "
                f"TypeScript {round(100.0 * typescript_overall / per_language_total, 1)}%"
            ),
            "significance_or_status": "Contradicted on the current matched panel",
            "verdict": "not_established",
        },
        {
            "claim": "Control-flow explicitness is the primary isolated driver.",
            "evidence": "Suite D paper-grade ablation + leave-one-out proxy analysis",
            "estimator": "Paired deltas and correlation sensitivity",
            "effect": "All suite deltas within +/-3 points",
            "significance_or_status": "Not Holm-significant; outlier-sensitive proxy",
            "verdict": "not_established",
        },
        {
            "claim": "Explicit result contracts and state flow are helpful secondary contributors.",
            "evidence": "Suites E and F",
            "estimator": "Paired deltas versus baseline",
            "effect": "Tagged tuples +3.0; state-flow variants +5.1 to +5.6",
            "significance_or_status": "Directional only after Holm correction",
            "verdict": "directional",
        },
    ]


def build_panel_stats(
    overall: list[dict],
    aggregate_conditions: list[dict],
    paired_rows: list[dict],
    by_task: list[dict],
    task_language: list[dict],
) -> dict:
    tasks_by_title: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    task_ids_to_titles: dict[str, str] = {}
    for row in task_language:
        task_ids_to_titles[row["task_id"]] = row["title"]
        tasks_by_title[row["task_id"]][row["language"]][row["condition_id"]] = row["success"]

    example_rescues: list[dict] = []
    for task_id, language_map in sorted(tasks_by_title.items()):
        rescue_languages = []
        for language, conditions in sorted(language_map.items()):
            if conditions.get("rich_contract_examples", 0) == 1 and conditions.get("baseline_compact", 0) == 0:
                rescue_languages.append(language)
        if rescue_languages:
            example_rescues.append(
                {
                    "task_id": task_id,
                    "title": task_ids_to_titles[task_id],
                    "languages": rescue_languages,
                }
            )

    return {
        "overall": overall,
        "aggregate_conditions": aggregate_conditions,
        "paired": paired_rows,
        "by_task": by_task,
        "example_rescues": example_rescues,
    }


def write_summary_markdown(
    overall: list[dict],
    aggregate_conditions: list[dict],
    paired_language: list[dict],
    paired_all: list[dict],
    panel_stats: dict,
) -> None:
    lines = [
        "# Explicit Task Panel Results",
        "",
        "## Language By Condition",
        "",
    ]
    for row in overall:
        lines.append(
            f"- `{row['language']} / {row['condition_id']}`: `{row['passed']}/{row['total']} = {row['pass_rate']}%` "
            f"(95% Wilson CI `{row['ci_low']}%` to `{row['ci_high']}%`)."
        )

    lines.extend(["", "## Aggregate Condition Totals", ""])
    for row in aggregate_conditions:
        lines.append(
            f"- `{row['condition_id']}`: `{row['passed']}/{row['total']} = {row['pass_rate']}%` "
            f"(95% Wilson CI `{row['ci_low']}%` to `{row['ci_high']}%`)."
        )

    lines.extend(["", "## Paired Cross-Language Comparisons", ""])
    for row in paired_all:
        lines.append(
            f"- `{row['comparison']}`: mean paired delta `{row['mean_task_delta']}`, "
            f"wins `{row['left_only_wins']}` vs losses `{row['right_only_wins']}`, "
            f"discordant pairs `{row['discordant_n']}`, exact sign p `{row['sign_test_p']}`."
        )

    lines.extend(["", "## Per-Language Paired Comparisons", ""])
    for row in paired_language:
        lines.append(
            f"- `{row['language']} / {row['comparison']}`: mean task delta `{row['mean_task_delta']}`, "
            f"wins `{row['left_only_wins']}` vs losses `{row['right_only_wins']}`, "
            f"tied pass `{row['tied_pass']}`, tied fail `{row['tied_fail']}`, exact sign p `{row['sign_test_p']}`."
        )

    lines.extend(["", "## Tasks Rescued By Examples", ""])
    if panel_stats["example_rescues"]:
        for row in panel_stats["example_rescues"]:
            lines.append(
                f"- `{row['title']}` (`{row['task_id']}`): rescued for `{', '.join(row['languages'])}`."
            )
    else:
        lines.append("- None.")

    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_task_appendix(task_language: list[dict]) -> None:
    grouped: dict[tuple[str, str], dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
    for row in task_language:
        grouped[(row["task_id"], row["title"])][row["language"]][row["condition_id"]] = row["success"]

    lines = [
        "# Explicit Task Panel Appendix",
        "",
        "Each row shows whether GPT-5.4 medium passed (`1`) or failed (`0`) for the language-task pair under each framing condition.",
        "",
    ]

    for (task_id, title), language_map in sorted(grouped.items()):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Task id: `{task_id}`")
        lines.append("")
        lines.append("| Language | baseline_compact | rich_contract | rich_contract_examples |")
        lines.append("| --- | ---: | ---: | ---: |")
        for language, conditions in sorted(language_map.items()):
            lines.append(
                f"| {language} | {conditions.get('baseline_compact', 0)} | {conditions.get('rich_contract', 0)} | {conditions.get('rich_contract_examples', 0)} |"
            )
        lines.append("")

    (RESULTS_DIR / "task_appendix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    overall = overall_rows(rows)
    aggregate_conditions = aggregate_condition_rows(rows)
    fixed = task_fixed_rows(rows)
    paired = aggregate_paired_rows(rows)
    task_rows = by_task_rows(rows)
    task_language = task_language_rows(rows)
    claims = claims_rows(overall, paired)
    panel_stats = build_panel_stats(overall, aggregate_conditions, paired, task_rows, task_language)

    write_csv(RESULTS_DIR / "overall.csv", overall)
    write_csv(RESULTS_DIR / "aggregate_conditions.csv", aggregate_conditions)
    write_csv(RESULTS_DIR / "task_fixed.csv", fixed)
    write_csv(RESULTS_DIR / "paired_stats.csv", paired)
    write_csv(RESULTS_DIR / "by_task.csv", task_rows)
    write_csv(RESULTS_DIR / "task_language_results.csv", task_language)
    write_csv(RESULTS_DIR / "claims_table.csv", claims)
    write_task_appendix(task_language)
    write_summary_markdown(overall, aggregate_conditions, fixed, paired, panel_stats)
    (RESULTS_DIR / "panel_stats.json").write_text(json.dumps(panel_stats, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
