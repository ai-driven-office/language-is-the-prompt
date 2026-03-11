#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PANEL_ROWS = REPO_ROOT / "results" / "explicit_task_panel" / "task_language_results.csv"
FACTORIAL_ROWS = REPO_ROOT / "results" / "explicit_task_factorial" / "row_level_results.csv"
OUTPUT_DIR = REPO_ROOT / "results" / "elixir_quick_robustness"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = (len(sorted_values) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def bootstrap_ci(samples: list[float], low_q: float = 0.025, high_q: float = 0.975) -> tuple[float, float]:
    ordered = sorted(samples)
    return percentile(ordered, low_q), percentile(ordered, high_q)


def format_float(value: float) -> str:
    return f"{value:+.3f}"


def panel_robustness() -> dict[str, object]:
    rows = read_csv(PANEL_ROWS)
    by_pair: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    titles: dict[str, str] = {}
    for row in rows:
        task_id = row["task_id"]
        language = row["language"]
        condition = row["condition_id"]
        titles[task_id] = row["title"]
        by_pair[(task_id, language)][condition] = int(row["success"])

    deltas: list[dict[str, object]] = []
    tasks = sorted({task_id for task_id, _ in by_pair})
    languages = sorted({language for _, language in by_pair})
    for (task_id, language), values in sorted(by_pair.items()):
        deltas.append(
            {
                "task_id": task_id,
                "title": titles[task_id],
                "language": language,
                "delta": values["rich_contract_examples"] - values["baseline_compact"],
            }
        )

    overall = sum(item["delta"] for item in deltas) / len(deltas)

    rng = random.Random(0)
    boot = []
    for _ in range(10_000):
        sampled_tasks = [rng.choice(tasks) for _ in tasks]
        sampled = []
        for task_id in sampled_tasks:
            sampled.extend(item["delta"] for item in deltas if item["task_id"] == task_id)
        boot.append(sum(sampled) / len(sampled))
    ci_low, ci_high = bootstrap_ci(boot)

    leave_one_task_out = []
    for task_id in tasks:
        subset = [item["delta"] for item in deltas if item["task_id"] != task_id]
        leave_one_task_out.append(
            {
                "omitted": task_id,
                "title": titles[task_id],
                "delta": sum(subset) / len(subset),
            }
        )

    leave_one_language_out = []
    for language in languages:
        subset = [item["delta"] for item in deltas if item["language"] != language]
        leave_one_language_out.append(
            {
                "omitted": language,
                "delta": sum(subset) / len(subset),
            }
        )

    return {
        "study": "explicit_task_panel",
        "comparison": "rich_contract_examples_vs_baseline_compact",
        "overall_delta": overall,
        "task_bootstrap_ci": [ci_low, ci_high],
        "leave_one_task_out": leave_one_task_out,
        "leave_one_language_out": leave_one_language_out,
    }


def factorial_robustness() -> dict[str, object]:
    rows = read_csv(FACTORIAL_ROWS)
    condition_factors: dict[str, dict[str, int]] = {}
    result_map: dict[tuple[str, str, str], int] = {}
    tasks = sorted({row["task_id"] for row in rows})
    languages = sorted({row["language"] for row in rows})
    titles: dict[str, str] = {}

    for row in rows:
        task_id = row["task_id"]
        language = row["language"]
        condition_id = row["condition_id"]
        result_map[(task_id, language, condition_id)] = int(row["success"])
        titles[task_id] = row["title"]
        if condition_id not in condition_factors:
            condition_factors[condition_id] = {
                factor: int(row[factor])
                for factor in ("docs_rich", "examples", "contracts_explicit", "state_guidance")
            }

    condition_ids = sorted(condition_factors)

    def effect_for_factor(
        factor: str,
        omit_task: str | None = None,
        omit_language: str | None = None,
    ) -> float:
        pair_deltas = []
        for task_id in tasks:
            if task_id == omit_task:
                continue
            for language in languages:
                if language == omit_language:
                    continue
                plus = []
                minus = []
                for condition_id in condition_ids:
                    outcome = result_map[(task_id, language, condition_id)]
                    if condition_factors[condition_id][factor] == 1:
                        plus.append(outcome)
                    else:
                        minus.append(outcome)
                pair_deltas.append(sum(plus) / len(plus) - sum(minus) / len(minus))
        return sum(pair_deltas) / len(pair_deltas)

    rng = random.Random(0)
    effects = []
    for factor in ("docs_rich", "examples", "contracts_explicit", "state_guidance"):
        bootstrap = []
        for _ in range(10_000):
            sampled_tasks = [rng.choice(tasks) for _ in tasks]
            pair_deltas = []
            for task_id in sampled_tasks:
                for language in languages:
                    plus = []
                    minus = []
                    for condition_id in condition_ids:
                        outcome = result_map[(task_id, language, condition_id)]
                        if condition_factors[condition_id][factor] == 1:
                            plus.append(outcome)
                        else:
                            minus.append(outcome)
                    pair_deltas.append(sum(plus) / len(plus) - sum(minus) / len(minus))
            bootstrap.append(sum(pair_deltas) / len(pair_deltas))
        ci_low, ci_high = bootstrap_ci(bootstrap)

        leave_task = [
            {
                "omitted": task_id,
                "title": titles[task_id],
                "delta": effect_for_factor(factor, omit_task=task_id),
            }
            for task_id in tasks
        ]
        leave_language = [
            {
                "omitted": language,
                "delta": effect_for_factor(factor, omit_language=language),
            }
            for language in languages
        ]

        effects.append(
            {
                "factor": factor,
                "overall_delta": effect_for_factor(factor),
                "task_bootstrap_ci": [ci_low, ci_high],
                "leave_one_task_out": leave_task,
                "leave_one_language_out": leave_language,
            }
        )

    return {
        "study": "explicit_task_factorial",
        "effects": effects,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(panel: dict[str, object], factorial: dict[str, object]) -> None:
    lines = [
        "# Quick Robustness Checks",
        "",
        "These analyses reuse existing matched-study outputs. No new model generations are required.",
        "",
        "## Explicit-Task Panel",
        "",
        f"- Comparison: `{panel['comparison']}`",
        f"- Overall matched mean delta: `{panel['overall_delta']:.3f}`",
        f"- Task-cluster bootstrap 95% CI: `{panel['task_bootstrap_ci'][0]:+.3f}` to `{panel['task_bootstrap_ci'][1]:+.3f}`",
        f"- Leave-one-task-out delta range: `{min(row['delta'] for row in panel['leave_one_task_out']):+.3f}` to `{max(row['delta'] for row in panel['leave_one_task_out']):+.3f}`",
        f"- Leave-one-language-out delta range: `{min(row['delta'] for row in panel['leave_one_language_out']):+.3f}` to `{max(row['delta'] for row in panel['leave_one_language_out']):+.3f}`",
        "",
        "Interpretation: the examples effect remains directionally positive, but the bootstrap interval crosses zero and the leave-one-language-out deltas shrink substantially. This remains a low-power, non-decisive signal.",
        "",
        "## Explicit-Task Factorial",
        "",
        "| Factor | Overall delta | Task-bootstrap 95% CI | Leave-one-task-out range | Leave-one-language-out range |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for effect in factorial["effects"]:
        leave_task = effect["leave_one_task_out"]
        leave_language = effect["leave_one_language_out"]
        lines.append(
            f"| `{effect['factor']}` | `{effect['overall_delta']:+.3f}` | "
            f"`{effect['task_bootstrap_ci'][0]:+.3f}` to `{effect['task_bootstrap_ci'][1]:+.3f}` | "
            f"`{min(row['delta'] for row in leave_task):+.3f}` to `{max(row['delta'] for row in leave_task):+.3f}` | "
            f"`{min(row['delta'] for row in leave_language):+.3f}` to `{max(row['delta'] for row in leave_language):+.3f}` |"
        )
    lines.extend(
        [
            "",
            "Interpretation: the explicit-contract effect is the most stable same-task result in the current paper. It remains positive under every single-task omission and every single-language omission, and its task-cluster bootstrap interval stays above zero. The examples effect is also consistently positive under these robustness checks, but it still falls short of Holm-corrected significance in the primary paired test.",
            "",
        ]
    )
    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = panel_robustness()
    factorial = factorial_robustness()

    (OUTPUT_DIR / "robustness.json").write_text(
        json.dumps({"panel": panel, "factorial": factorial}, indent=2) + "\n",
        encoding="utf-8",
    )

    write_csv(
        OUTPUT_DIR / "panel_leave_one_task_out.csv",
        panel["leave_one_task_out"],
        ["omitted", "title", "delta"],
    )
    write_csv(
        OUTPUT_DIR / "panel_leave_one_language_out.csv",
        panel["leave_one_language_out"],
        ["omitted", "delta"],
    )

    factorial_rows = []
    for effect in factorial["effects"]:
        factorial_rows.append(
            {
                "factor": effect["factor"],
                "overall_delta": f"{effect['overall_delta']:.6f}",
                "bootstrap_ci_low": f"{effect['task_bootstrap_ci'][0]:.6f}",
                "bootstrap_ci_high": f"{effect['task_bootstrap_ci'][1]:.6f}",
                "loo_task_min": f"{min(row['delta'] for row in effect['leave_one_task_out']):.6f}",
                "loo_task_max": f"{max(row['delta'] for row in effect['leave_one_task_out']):.6f}",
                "loo_language_min": f"{min(row['delta'] for row in effect['leave_one_language_out']):.6f}",
                "loo_language_max": f"{max(row['delta'] for row in effect['leave_one_language_out']):.6f}",
            }
        )
    write_csv(
        OUTPUT_DIR / "factorial_robustness.csv",
        factorial_rows,
        [
            "factor",
            "overall_delta",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
            "loo_task_min",
            "loo_task_max",
            "loo_language_min",
            "loo_language_max",
        ],
    )

    write_markdown(panel, factorial)
    print(f"Wrote {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
