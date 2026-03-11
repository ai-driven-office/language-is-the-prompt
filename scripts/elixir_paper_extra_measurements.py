#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
ACTIVE_DIR = RESULTS_DIR / "elixir_active_suites"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def rankdata(values: list[float]) -> list[float]:
    ordered = sorted((value, idx) for idx, value in enumerate(values))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        avg_rank = (start + 1 + end) / 2.0
        for _, idx in ordered[start:end]:
            ranks[idx] = avg_rank
        start = end
    return ranks


def pearson(values_x: list[float], values_y: list[float]) -> float:
    mean_x = statistics.mean(values_x)
    mean_y = statistics.mean(values_y)
    var_x = sum((value - mean_x) ** 2 for value in values_x)
    var_y = sum((value - mean_y) ** 2 for value in values_y)
    if var_x == 0.0 or var_y == 0.0:
        return 0.0
    cov = sum((value_x - mean_x) * (value_y - mean_y) for value_x, value_y in zip(values_x, values_y))
    return cov / math.sqrt(var_x * var_y)


def spearman(values_x: list[float], values_y: list[float]) -> float:
    return pearson(rankdata(values_x), rankdata(values_y))


def exact_binomial_two_sided(baseline_only: int, condition_only: int) -> float:
    n = baseline_only + condition_only
    if n == 0:
        return 1.0
    k = min(baseline_only, condition_only)
    cumulative = 0.0
    for index in range(0, k + 1):
        cumulative += math.comb(n, index) * (0.5**n)
    return min(1.0, 2.0 * cumulative)


def holm_adjust(pvalues: list[float]) -> list[float]:
    indexed = sorted(enumerate(pvalues), key=lambda item: item[1])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    total = len(pvalues)
    for rank, (original_index, value) in enumerate(indexed, start=1):
        candidate = min(1.0, (total - rank + 1) * value)
        running = max(running, candidate)
        adjusted[original_index] = running
    return adjusted


def load_language_metrics() -> dict[str, dict[str, float]]:
    suite_a = read_csv(RESULTS_DIR / "elixir_suite_a" / "suite_a_docs_quality.csv")
    rows: dict[str, dict[str, float]] = {
        row["language"]: {
            "pass_rate": float(row["pass_rate"]),
            "docs_score": float(row["mean_docs_score"]),
            "question_chars": float(row["mean_question_chars"]),
            "example_markers": float(row["mean_example_markers"]),
        }
        for row in suite_a
    }

    enrichments = [
        (RESULTS_DIR / "elixir_suite_b" / "suite_b_corpus_quality.csv", {"cleanliness": "mean_cleanliness_score"}),
        (RESULTS_DIR / "elixir_suite_c" / "suite_c_stylistic_entropy.csv", {"style_stability": "mean_style_stability_score", "style_entropy": "mean_style_entropy"}),
        (RESULTS_DIR / "elixir_suite_d" / "suite_d_control_flow.csv", {"control_flow_score": "mean_control_flow_score"}),
        (RESULTS_DIR / "elixir_suite_e" / "suite_e_result_contracts.csv", {"contract_score": "mean_contract_score", "tagged_tuple_count": "mean_tagged_tuple_count"}),
        (RESULTS_DIR / "elixir_suite_f" / "suite_f_mutability.csv", {"mutability_burden": "mean_mutability_burden_score"}),
        (RESULTS_DIR / "elixir_suite_g" / "suite_g_alignment.csv", {"alignment_score": "mean_alignment_score"}),
    ]

    for path, field_map in enrichments:
        for row in read_csv(path):
            language = row["language"]
            if language not in rows:
                continue
            for output_key, input_key in field_map.items():
                rows[language][output_key] = float(row[input_key])
    return rows


def compute_cross_language_correlations(language_rows: dict[str, dict[str, float]]) -> tuple[list[dict], list[dict]]:
    languages = sorted(language_rows)
    pass_rates = [language_rows[language]["pass_rate"] for language in languages]
    metric_order = [
        "docs_score",
        "cleanliness",
        "style_stability",
        "style_entropy",
        "control_flow_score",
        "contract_score",
        "mutability_burden",
        "alignment_score",
        "question_chars",
        "example_markers",
    ]
    rows: list[dict] = []
    for metric in metric_order:
        values = [language_rows[language][metric] for language in languages]
        rows.append(
            {
                "metric": metric,
                "pearson_all": round(pearson(values, pass_rates), 3),
                "spearman_all": round(spearman(values, pass_rates), 3),
            }
        )

    composite_rows: list[dict] = []
    for exclude_elixir in (False, True):
        selected = [language for language in languages if not exclude_elixir or language != "elixir"]
        pass_subset = [language_rows[language]["pass_rate"] for language in selected]
        z_components: list[list[float]] = []
        for metric, sign in (("control_flow_score", 1.0), ("contract_score", 1.0), ("mutability_burden", -1.0)):
            raw = [language_rows[language][metric] * sign for language in selected]
            mean = statistics.mean(raw)
            stddev = statistics.pstdev(raw) or 1.0
            z_components.append([(value - mean) / stddev for value in raw])
        composite = [sum(values) for values in zip(*z_components)]
        composite_rows.append(
            {
                "cohort": "exclude_elixir" if exclude_elixir else "all_languages",
                "pearson": round(pearson(composite, pass_subset), 3),
                "spearman": round(spearman(composite, pass_subset), 3),
            }
        )
    return rows, composite_rows


def compute_leave_one_out_influence(language_rows: dict[str, dict[str, float]]) -> list[dict]:
    languages = sorted(language_rows)
    metrics = ["docs_score", "control_flow_score", "mutability_burden", "contract_score"]
    rows: list[dict] = []
    for metric in metrics:
        full_x = [language_rows[language][metric] for language in languages]
        full_y = [language_rows[language]["pass_rate"] for language in languages]
        full_pearson = pearson(full_x, full_y)
        full_spearman = spearman(full_x, full_y)
        for excluded in languages:
            subset = [language for language in languages if language != excluded]
            values_x = [language_rows[language][metric] for language in subset]
            values_y = [language_rows[language]["pass_rate"] for language in subset]
            loo_pearson = pearson(values_x, values_y)
            loo_spearman = spearman(values_x, values_y)
            rows.append(
                {
                    "metric": metric,
                    "excluded_language": excluded,
                    "pearson_without_language": round(loo_pearson, 3),
                    "delta_pearson": round(loo_pearson - full_pearson, 3),
                    "spearman_without_language": round(loo_spearman, 3),
                    "delta_spearman": round(loo_spearman - full_spearman, 3),
                }
            )
    return rows


def read_summary_map(suite_id: str) -> dict[str, dict[str, str]]:
    return {row["condition"]: row for row in read_csv(ACTIVE_DIR / f"{suite_id}_summary.csv")}


def read_paired_map(suite_id: str) -> dict[str, dict[str, str]]:
    path = ACTIVE_DIR / f"{suite_id}_paired_stats.csv"
    if not path.exists():
        return {}
    return {row["condition"]: row for row in read_csv(path)}


def compute_intervention_effects() -> list[dict]:
    suite_titles = {
        "suite_a": "Documentation Quality",
        "suite_d": "Pattern Matching and Control Flow",
        "suite_e": "Result Contracts",
        "suite_f": "Mutability and State Style",
    }
    baseline_names = {"suite_a": "full_docs", "suite_d": "baseline", "suite_e": "baseline", "suite_f": "baseline"}
    rows: list[dict] = []
    for suite_id, suite_title in suite_titles.items():
        summary_map = read_summary_map(suite_id)
        paired_map = read_paired_map(suite_id)
        baseline_name = baseline_names[suite_id]
        for condition, row in summary_map.items():
            if condition == baseline_name:
                continue
            paired = paired_map.get(condition, {})
            rows.append(
                {
                    "suite_id": suite_id,
                    "suite_title": suite_title,
                    "condition": condition,
                    "pass_rate": float(row["pass_rate"]),
                    "delta_vs_baseline": float(row["delta_vs_baseline"]),
                    "ci_low": float(row["ci_low"]) if "ci_low" in row else "",
                    "ci_high": float(row["ci_high"]) if "ci_high" in row else "",
                    "mcnemar_pvalue": float(paired["mcnemar_pvalue"]) if paired else "",
                    "delta_ci_low": float(paired["delta_ci_low"]) if paired else "",
                    "delta_ci_high": float(paired["delta_ci_high"]) if paired else "",
                    "baseline_only_wins": int(paired["baseline_only_wins"]) if paired else "",
                    "condition_only_wins": int(paired["condition_only_wins"]) if paired else "",
                    "matched_odds_ratio": round(
                        (int(paired["condition_only_wins"]) + 0.5) / (int(paired["baseline_only_wins"]) + 0.5),
                        3,
                    ) if paired else "",
                    "risk_ratio_vs_baseline": round(
                        float(row["pass_rate"]) / float(summary_map[baseline_name]["pass_rate"]),
                        3,
                    ),
                }
            )
    pvalues = [float(row["mcnemar_pvalue"]) for row in rows if row["mcnemar_pvalue"] != ""]
    adjusted = holm_adjust(pvalues)
    index = 0
    for row in rows:
        if row["mcnemar_pvalue"] == "":
            row["holm_adjusted_pvalue"] = ""
            row["holm_significant_05"] = ""
            continue
        row["holm_adjusted_pvalue"] = round(adjusted[index], 6)
        row["holm_significant_05"] = adjusted[index] <= 0.05
        index += 1
    rows.sort(key=lambda row: row["delta_vs_baseline"])
    return rows


def compute_suite_a_docs_difficulty() -> list[dict]:
    by_difficulty = read_csv(ACTIVE_DIR / "suite_a_by_difficulty.csv")
    task_rows = read_csv(ACTIVE_DIR / "suite_a_task_comparisons.csv")

    baseline_rates = {
        row["difficulty"]: float(row["pass_rate"])
        for row in by_difficulty
        if row["condition"] == "full_docs"
    }

    outcome_counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in task_rows:
        outcome_counts[(row["condition"], row["difficulty"])][row["outcome"]] += 1

    rows: list[dict] = []
    for row in by_difficulty:
        condition = row["condition"]
        if condition == "full_docs":
            continue
        difficulty = row["difficulty"]
        counts = outcome_counts[(condition, difficulty)]
        rows.append(
            {
                "condition": condition,
                "difficulty": difficulty,
                "pass_rate": float(row["pass_rate"]),
                "baseline_pass_rate": baseline_rates[difficulty],
                "delta_vs_full_docs": round(float(row["pass_rate"]) - baseline_rates[difficulty], 1),
                "baseline_only_wins": counts["baseline_only"],
                "condition_only_wins": counts["condition_only"],
                "same": counts["same"],
                "mcnemar_pvalue": round(exact_binomial_two_sided(counts["baseline_only"], counts["condition_only"]), 6),
            }
        )
    return rows


def write_markdown_summary(
    correlation_rows: list[dict],
    composite_rows: list[dict],
    intervention_rows: list[dict],
    docs_rows: list[dict],
    influence_rows: list[dict],
) -> None:
    strongest_negative = sorted(intervention_rows, key=lambda row: row["delta_vs_baseline"])[0]
    strongest_positive = sorted(intervention_rows, key=lambda row: row["delta_vs_baseline"], reverse=True)[0]
    suite_a_hard = next(row for row in docs_rows if row["condition"] == "signature_only" and row["difficulty"] == "hard")
    suite_a_hard_min = next(row for row in docs_rows if row["condition"] == "minimal_docs" and row["difficulty"] == "hard")
    docs_corr = next(row for row in correlation_rows if row["metric"] == "docs_score")
    cf_corr = next(row for row in correlation_rows if row["metric"] == "control_flow_score")
    mut_corr = next(row for row in correlation_rows if row["metric"] == "mutability_burden")
    composite_all = next(row for row in composite_rows if row["cohort"] == "all_languages")
    composite_ex = next(row for row in composite_rows if row["cohort"] == "exclude_elixir")
    control_flow_elixir = next(
        row for row in influence_rows if row["metric"] == "control_flow_score" and row["excluded_language"] == "elixir"
    )
    docs_elixir = next(
        row for row in influence_rows if row["metric"] == "docs_score" and row["excluded_language"] == "elixir"
    )
    holm_significant = [row for row in intervention_rows if row["holm_significant_05"] is True]

    lines = [
        "# Extra Measurements For The Elixir Paper",
        "",
        "## High-signal additions",
        "",
        f"- The strongest active effect in the completed study is still documentation structure removal: `{strongest_negative['condition']}` in `{strongest_negative['suite_id']}` moves pass rate by `{strongest_negative['delta_vs_baseline']}` points.",
        f"- The strongest positive active effect is `{strongest_positive['condition']}` in `{strongest_positive['suite_id']}` at `{strongest_positive['delta_vs_baseline']}` points, but those gains are much smaller than the docs losses.",
        f"- On hard Elixir tasks, `signature_only` drops to `{suite_a_hard['pass_rate']}%` from `84.2%` full-docs baseline, with McNemar `p={suite_a_hard['mcnemar_pvalue']}`.",
        f"- On hard Elixir tasks, `minimal_docs` drops to `{suite_a_hard_min['pass_rate']}%` from `84.2%`, with McNemar `p={suite_a_hard_min['mcnemar_pvalue']}`.",
        "",
        "## Cross-language proxy read",
        "",
        f"- Cross-language documentation proxy is only a weak-to-moderate correlate of pass rate: Spearman `{docs_corr['spearman_all']}`, Pearson `{docs_corr['pearson_all']}`.",
        f"- Control-flow proxy is directionally strongest in Pearson space: Spearman `{cf_corr['spearman_all']}`, Pearson `{cf_corr['pearson_all']}`.",
        f"- Mutability burden is only moderately negative: Spearman `{mut_corr['spearman_all']}`, Pearson `{mut_corr['pearson_all']}`.",
        f"- The three-part explicitness composite correlates with pass rate across all 20 languages at Pearson `{composite_all['pearson']}`, but collapses without Elixir to Pearson `{composite_ex['pearson']}`.",
        f"- Leaving Elixir out moves control-flow Pearson from `{cf_corr['pearson_all']}` to `{control_flow_elixir['pearson_without_language']}`, showing how much the current cross-language control-flow result depends on the Elixir outlier.",
        f"- Leaving Elixir out moves documentation Pearson from `{docs_corr['pearson_all']}` to `{docs_elixir['pearson_without_language']}`, which is much less dramatic.",
        "",
        "## Multiple-testing control",
        "",
        f"- After Holm correction across all active interventions, `{len(holm_significant)}` contrasts remain significant at 0.05.",
        "- The surviving signals are the large documentation-structure degradations, not the smaller control-flow or contract perturbations.",
        "",
        "## What the draft should tighten",
        "",
        "- Do not keep the old claim that documentation is not explanatory in any important sense. The full paper-scale Suite A now shows that rich task framing is a major within-language driver.",
        "- Keep the narrower claim instead: cross-language docs-quality proxies do not explain why Elixir beats every other language, because Elixir is not top-ranked on those proxies.",
        "- Soften the causal claims for pattern matching and tagged tuples. The full active reruns are much weaker there than the earlier pilot suggested.",
        "- Reframe the state-style claim from 'immutability is the direct cause' to 'explicit state transitions matter more than hidden mutable state.'",
        "",
        "## Recommended thesis update",
        "",
        "Elixir's advantage is best framed as an explicitness-and-legibility effect with two tiers:",
        "",
        "1. Strong evidence: rich documentation structure and explicit task framing make correct continuations much easier to predict.",
        "2. Directional but weaker evidence: control-flow explicitness, result-shape conventions, and explicit state flow likely help, but the full active ablations do not justify treating them as equally established causal drivers yet.",
        "",
    ]
    output_path = RESULTS_DIR / "elixir_paper_extra_measurements.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_yaml_payload(
    correlation_rows: list[dict],
    composite_rows: list[dict],
    intervention_rows: list[dict],
    docs_rows: list[dict],
    influence_rows: list[dict],
) -> None:
    payload = {
        "cross_language_correlations": correlation_rows,
        "explicitness_composite": composite_rows,
        "active_intervention_effects": intervention_rows,
        "suite_a_docs_by_difficulty": docs_rows,
        "leave_one_out_influence": influence_rows,
    }
    path = RESULTS_DIR / "elixir_paper_extra_measurements.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    language_rows = load_language_metrics()
    correlation_rows, composite_rows = compute_cross_language_correlations(language_rows)
    influence_rows = compute_leave_one_out_influence(language_rows)
    intervention_rows = compute_intervention_effects()
    docs_rows = compute_suite_a_docs_difficulty()

    write_csv(RESULTS_DIR / "elixir_paper_cross_language_correlations.csv", correlation_rows)
    write_csv(RESULTS_DIR / "elixir_paper_explicitness_composite.csv", composite_rows)
    write_csv(RESULTS_DIR / "elixir_paper_leave_one_out_influence.csv", influence_rows)
    write_csv(RESULTS_DIR / "elixir_paper_intervention_effects.csv", intervention_rows)
    write_csv(RESULTS_DIR / "elixir_paper_docs_difficulty.csv", docs_rows)
    write_markdown_summary(correlation_rows, composite_rows, intervention_rows, docs_rows, influence_rows)
    write_yaml_payload(correlation_rows, composite_rows, intervention_rows, docs_rows, influence_rows)


if __name__ == "__main__":
    main()
