#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXEC_PATH = REPO_ROOT / "outputs" / "openai-5-4-medium-adaptive.native-fixed.exec.jsonl"
RESULTS_DIR = REPO_ROOT / "results"

GENERIC_TITLES = {"", "problem description", "problem description:", "<problemdescription>"}


def normalize_title(question: str) -> str:
    first_line = question.splitlines()[0].strip().lower()
    first_line = re.sub(r"^#+\s*", "", first_line)
    first_line = re.sub(r"^\*\*", "", first_line)
    first_line = re.sub(r"\*\*$", "", first_line)
    first_line = re.sub(r"^(problem description:|problem:|exercise:|task:)\s*", "", first_line)
    first_line = re.sub(r"[`\"“”‘’*_()]", "", first_line)
    first_line = re.sub(r"\s+", " ", first_line)
    return first_line.strip()


def extract_title(question: str) -> str:
    return question.splitlines()[0].strip()


def load_rows() -> list[dict]:
    rows: list[dict] = []
    with EXEC_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            original = row["original_data"]
            rows.append(
                {
                    "index": row["index"],
                    "language": row["language"],
                    "success": int(bool(row["success"])),
                    "difficulty": original.get("difficulty", ""),
                    "question": original["question"],
                    "title_raw": extract_title(original["question"]),
                    "title_norm": normalize_title(original["question"]),
                }
            )
    return rows


def identify_clusters(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_title: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["title_norm"] in GENERIC_TITLES:
            continue
        by_title[row["title_norm"]].append(row)

    clusters: list[dict] = []
    cluster_rows: list[dict] = []
    cluster_id = 0
    for title_norm, title_rows in sorted(by_title.items()):
        language_counts = Counter(row["language"] for row in title_rows)
        if len(language_counts) < 2 or max(language_counts.values()) > 1:
            continue
        cluster_id += 1
        title_display = min((row["title_raw"] for row in title_rows), key=len)
        languages = sorted(row["language"] for row in title_rows)
        difficulties = sorted(set(row["difficulty"] for row in title_rows))
        cluster_name = f"cluster_{cluster_id:03d}"
        clusters.append(
            {
                "cluster_id": cluster_name,
                "title_norm": title_norm,
                "title_display": title_display,
                "languages": ",".join(languages),
                "n_languages": len(languages),
                "difficulty_set": ",".join(difficulties),
                "difficulty_span": len(difficulties),
            }
        )
        for row in title_rows:
            cluster_rows.append(
                {
                    "cluster_id": cluster_name,
                    "title_norm": title_norm,
                    "title_display": title_display,
                    "language": row["language"],
                    "difficulty": row["difficulty"],
                    "success": row["success"],
                    "index": row["index"],
                }
            )
    return clusters, cluster_rows


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    position = q * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def bootstrap_ci(values: list[float], samples: int = 5000, seed: int = 54) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(samples):
        picked = [rng.choice(values) for _ in values]
        means.append(sum(picked) / len(picked))
    means.sort()
    return percentile(means, 0.025), percentile(means, 0.975)


def exact_sign_test_pvalue(positive: int, negative: int) -> float:
    n = positive + negative
    if n == 0:
        return 1.0
    k = min(positive, negative)
    cumulative = 0.0
    for value in range(0, k + 1):
        cumulative += math.comb(n, value) * (0.5**n)
    return min(1.0, 2.0 * cumulative)


def compute_language_effects(cluster_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_cluster: dict[str, list[dict]] = defaultdict(list)
    for row in cluster_rows:
        by_cluster[row["cluster_id"]].append(row)

    per_language_residuals: dict[str, list[float]] = defaultdict(list)
    language_cluster_count: Counter = Counter()
    for cluster_id, rows in by_cluster.items():
        cluster_mean = sum(row["success"] for row in rows) / len(rows)
        for row in rows:
            per_language_residuals[row["language"]].append(row["success"] - cluster_mean)
            language_cluster_count[row["language"]] += 1

    language_rows: list[dict] = []
    for language, residuals in sorted(per_language_residuals.items(), key=lambda item: (-sum(item[1]) / len(item[1]), item[0])):
        mean_residual = sum(residuals) / len(residuals)
        ci_low, ci_high = bootstrap_ci(residuals)
        language_rows.append(
            {
                "language": language,
                "matched_cluster_count": language_cluster_count[language],
                "task_fixed_effect_residual": round(mean_residual, 4),
                "bootstrap_ci_low": round(ci_low, 4),
                "bootstrap_ci_high": round(ci_high, 4),
            }
        )

    elixir_rows = [rows for rows in by_cluster.values() if any(row["language"] == "elixir" for row in rows)]
    elixir_advantages: list[float] = []
    detail_rows: list[dict] = []
    for rows in elixir_rows:
        elixir_row = next(row for row in rows if row["language"] == "elixir")
        others = [row for row in rows if row["language"] != "elixir"]
        other_mean = sum(row["success"] for row in others) / len(others)
        advantage = elixir_row["success"] - other_mean
        elixir_advantages.append(advantage)
        detail_rows.append(
            {
                "cluster_id": elixir_row["cluster_id"],
                "title_display": elixir_row["title_display"],
                "elixir_success": elixir_row["success"],
                "other_language_mean_success": round(other_mean, 4),
                "elixir_advantage": round(advantage, 4),
                "other_languages": ",".join(sorted(row["language"] for row in others)),
            }
        )

    if elixir_advantages:
        positive = sum(1 for value in elixir_advantages if value > 0)
        negative = sum(1 for value in elixir_advantages if value < 0)
        zero = sum(1 for value in elixir_advantages if value == 0)
        ci_low, ci_high = bootstrap_ci(elixir_advantages)
        summary_row = {
            "cluster_count": len(elixir_advantages),
            "mean_elixir_advantage": round(sum(elixir_advantages) / len(elixir_advantages), 4),
            "bootstrap_ci_low": round(ci_low, 4),
            "bootstrap_ci_high": round(ci_high, 4),
            "positive_clusters": positive,
            "negative_clusters": negative,
            "tied_clusters": zero,
            "sign_test_pvalue": round(exact_sign_test_pvalue(positive, negative), 6),
        }
    else:
        summary_row = {
            "cluster_count": 0,
            "mean_elixir_advantage": 0.0,
            "bootstrap_ci_low": 0.0,
            "bootstrap_ci_high": 0.0,
            "positive_clusters": 0,
            "negative_clusters": 0,
            "tied_clusters": 0,
            "sign_test_pvalue": 1.0,
        }
    return language_rows, [summary_row, *detail_rows]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        import csv

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(clusters: list[dict], language_rows: list[dict], elixir_summary_rows: list[dict]) -> None:
    summary = elixir_summary_rows[0]
    lines = [
        "# Common-Task Fixed-Effects Analysis",
        "",
        "## Method",
        "",
        "- Because ACB-Full does not expose a shared task id across languages, this analysis uses a conservative recurring-task subset.",
        "- A task cluster is included only when multiple languages share the same exact normalized first-line title and each language appears at most once in that cluster.",
        f"- This yields `{len(clusters)}` high-confidence recurring-task clusters.",
        "- The task-fixed effect estimator is the within-cluster residual: `y_(l,c) - mean_c(y)`.",
        "- For Elixir-specific comparison, we compute `Delta_c = y_(elixir,c) - mean_(others in c)(y)` and bootstrap over clusters.",
        "",
        "## Key result",
        "",
        f"- Elixir appears in `{summary['cluster_count']}` recurring-task clusters.",
        f"- Mean within-cluster Elixir advantage is `{summary['mean_elixir_advantage']}` with bootstrap CI `{summary['bootstrap_ci_low']}` to `{summary['bootstrap_ci_high']}`.",
        f"- Sign test over non-tied clusters: `p={summary['sign_test_pvalue']}`.",
        "",
        "## Interpretation",
        "",
        "- This is a low-coverage sanity check, not a replacement for a benchmark with explicit shared task ids.",
        "- It is still useful because it removes some of the benchmark-composition ambiguity on the small subset where recurring tasks can be matched exactly by title.",
    ]
    output_path = RESULTS_DIR / "elixir_common_task_fixed_effects.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    clusters, cluster_rows = identify_clusters(rows)
    language_rows, elixir_summary_rows = compute_language_effects(cluster_rows)

    write_csv(RESULTS_DIR / "elixir_common_task_clusters.csv", clusters)
    write_csv(RESULTS_DIR / "elixir_common_task_cluster_rows.csv", cluster_rows)
    write_csv(RESULTS_DIR / "elixir_common_task_language_effects.csv", language_rows)
    write_csv(RESULTS_DIR / "elixir_common_task_elixir_summary.csv", elixir_summary_rows)
    write_markdown(clusters, language_rows, elixir_summary_rows)


if __name__ == "__main__":
    main()
