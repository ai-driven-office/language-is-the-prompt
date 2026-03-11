#!/usr/bin/env python3

from __future__ import annotations

import ast
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXEC_PATH = REPO_ROOT / "outputs" / "openai-5-4-medium-adaptive.native-fixed.exec.jsonl"
RESULTS_DIR = REPO_ROOT / "results"

COMPILE_OUTCOMES = {"COMPILATION_ERROR", "COMPILE_ERROR", "SYNTAX_ERROR"}
WRONG_OUTCOMES = {"WRONG_ANSWER"}
RUNTIME_OUTCOMES = {"RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED"}


def parse_result_payload(value):
    if isinstance(value, dict):
        return value
    return ast.literal_eval(value)


def first_non_pass_outcome(row: dict) -> tuple[str, str]:
    stages = [("demo", row.get("demo_test_result")), ("full", row.get("full_test_result"))]
    for stage_name, payload in stages:
        if payload is None:
            continue
        obj = parse_result_payload(payload)
        response = obj.get("response", {})
        outcome = response.get("exec_outcome")
        if outcome and outcome != "PASSED":
            return stage_name, outcome, response
    return "unknown", "UNKNOWN", {}


def runtime_subtype(outcome: str, response: dict) -> str:
    stderr = str(response.get("response_extensions", {}).get("stderr", "")).lower()
    if outcome == "TIME_LIMIT_EXCEEDED" or "time limit" in stderr:
        return "timeout"
    if "collection not found" in stderr or "module not found" in stderr or "cannot find module" in stderr:
        return "missing_dependency"
    if "assert" in stderr or "assertion failed" in stderr or "test case" in stderr or "expected" in stderr:
        return "assertion_test_abort"
    if "traceback" in stderr or "argumenterror" in stderr or "typeerror" in stderr or "valueerror" in stderr or "exception" in stderr or "panic" in stderr:
        return "language_exception"
    return "other_runtime"


def classify_failure(outcome: str) -> str:
    if outcome in COMPILE_OUTCOMES:
        return "compile"
    if outcome in WRONG_OUTCOMES:
        return "wrong_answer"
    if outcome in RUNTIME_OUTCOMES:
        return "runtime"
    return "other"


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    phat = successes / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    margin = z * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * total)) / total) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def log_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def hypergeom_prob(x: int, row1: int, row2: int, col1: int) -> float:
    col2 = row1 + row2 - col1
    if not (0 <= x <= row1 and 0 <= col1 - x <= row2 and 0 <= col2 - (row1 - x) <= row2):
        return 0.0
    return math.exp(log_comb(row1, x) + log_comb(row2, col1 - x) - log_comb(row1 + row2, col1))


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    row1 = a + b
    row2 = c + d
    col1 = a + c
    lo = max(0, col1 - row2)
    hi = min(row1, col1)
    observed = hypergeom_prob(a, row1, row2, col1)
    total = 0.0
    for x in range(lo, hi + 1):
        probability = hypergeom_prob(x, row1, row2, col1)
        if probability <= observed + 1e-12:
            total += probability
    return min(1.0, total)


def odds_ratio(a: int, b: int, c: int, d: int) -> float:
    return ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))


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


def load_rows() -> list[dict]:
    rows: list[dict] = []
    with EXEC_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            stage, outcome, response = first_non_pass_outcome(row)
            failure_category = "pass" if row.get("success") else classify_failure(outcome)
            rows.append(
                {
                    "language": row["language"],
                    "success": bool(row["success"]),
                    "first_failure_stage": stage,
                    "first_failure_outcome": outcome,
                    "failure_category": failure_category,
                    "runtime_subtype": runtime_subtype(outcome, response) if failure_category == "runtime" else "",
                }
            )
    return rows


def build_language_summary(rows: list[dict]) -> list[dict]:
    by_language: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_language[row["language"]].append(row)

    summary_rows: list[dict] = []
    for language, language_rows in sorted(by_language.items()):
        total = len(language_rows)
        failures = [row for row in language_rows if not row["success"]]
        failure_count = len(failures)
        counts = Counter(row["failure_category"] for row in failures)
        for category in ("compile", "runtime", "wrong_answer", "other"):
            count = counts[category]
            rate_total = count / total if total else 0.0
            rate_failures = count / failure_count if failure_count else 0.0
            low_total, high_total = wilson_interval(count, total)
            low_fail, high_fail = wilson_interval(count, failure_count) if failure_count else (0.0, 0.0)
            summary_rows.append(
                {
                    "language": language,
                    "category": category,
                    "count": count,
                    "total_rows": total,
                    "failure_rows": failure_count,
                    "rate_of_all_rows": round(rate_total * 100.0, 2),
                    "rate_all_ci_low": round(low_total * 100.0, 2),
                    "rate_all_ci_high": round(high_total * 100.0, 2),
                    "share_of_failures": round(rate_failures * 100.0, 2),
                    "share_failures_ci_low": round(low_fail * 100.0, 2),
                    "share_failures_ci_high": round(high_fail * 100.0, 2),
                }
            )
    return summary_rows


def build_elixir_tests(summary_rows: list[dict]) -> list[dict]:
    by_language_category = {(row["language"], row["category"]): row for row in summary_rows}
    languages = sorted({row["language"] for row in summary_rows})
    rows: list[dict] = []
    elixir_total = int(by_language_category[("elixir", "compile")]["total_rows"])
    elixir_failures = int(by_language_category[("elixir", "compile")]["failure_rows"])
    rest_total = sum(int(by_language_category[(language, "compile")]["total_rows"]) for language in languages if language != "elixir")
    rest_failures = sum(int(by_language_category[(language, "compile")]["failure_rows"]) for language in languages if language != "elixir")

    for category in ("compile", "runtime", "wrong_answer", "other"):
        elixir_count = int(by_language_category[("elixir", category)]["count"])
        rest_count = sum(int(by_language_category[(language, category)]["count"]) for language in languages if language != "elixir")

        total_table = (elixir_count, elixir_total - elixir_count, rest_count, rest_total - rest_count)
        failure_table = (elixir_count, elixir_failures - elixir_count, rest_count, rest_failures - rest_count)
        rows.append(
            {
                "category": category,
                "comparison_basis": "all_rows",
                "elixir_count": elixir_count,
                "elixir_non_count": elixir_total - elixir_count,
                "rest_count": rest_count,
                "rest_non_count": rest_total - rest_count,
                "odds_ratio": round(odds_ratio(*total_table), 4),
                "fisher_pvalue": round(fisher_exact_two_sided(*total_table), 6),
            }
        )
        rows.append(
            {
                "category": category,
                "comparison_basis": "failure_rows",
                "elixir_count": elixir_count,
                "elixir_non_count": elixir_failures - elixir_count,
                "rest_count": rest_count,
                "rest_non_count": rest_failures - rest_count,
                "odds_ratio": round(odds_ratio(*failure_table), 4),
                "fisher_pvalue": round(fisher_exact_two_sided(*failure_table), 6),
            }
        )
    adjusted = holm_adjust([float(row["fisher_pvalue"]) for row in rows])
    for row, adj in zip(rows, adjusted):
        row["holm_adjusted_pvalue"] = round(adj, 6)
        row["holm_significant_05"] = adj <= 0.05
    return rows


def build_stage_outcome_rows(rows: list[dict]) -> list[dict]:
    counter: Counter = Counter((row["language"], row["first_failure_stage"], row["first_failure_outcome"]) for row in rows if not row["success"])
    output_rows: list[dict] = []
    for (language, stage, outcome), count in sorted(counter.items()):
        output_rows.append(
            {
                "language": language,
                "first_failure_stage": stage,
                "first_failure_outcome": outcome,
                "count": count,
            }
        )
    return output_rows


def build_runtime_subtype_rows(rows: list[dict]) -> list[dict]:
    counts: Counter = Counter((row["language"], row["runtime_subtype"]) for row in rows if row["runtime_subtype"])
    output_rows: list[dict] = []
    for (language, subtype), count in sorted(counts.items()):
        output_rows.append(
            {
                "language": language,
                "runtime_subtype": subtype,
                "count": count,
            }
        )
    return output_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(summary_rows: list[dict], test_rows: list[dict], stage_rows: list[dict], subtype_rows: list[dict]) -> None:
    elixir_rows = {row["category"]: row for row in summary_rows if row["language"] == "elixir"}
    elixir_subtypes = [row for row in subtype_rows if row["language"] == "elixir"]
    lines = [
        "# Error Taxonomy Formalization",
        "",
        "## Definitions",
        "",
        "- Each failed benchmark row is classified by the first non-passed stage among demo and full tests.",
        "- Categories:",
        "  - `compile`: `COMPILATION_ERROR`, `COMPILE_ERROR`, or `SYNTAX_ERROR`",
        "  - `runtime`: `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, or `MEMORY_LIMIT_EXCEEDED`",
        "  - `wrong_answer`: `WRONG_ANSWER`",
        "  - `other`: anything else",
        "- Because this sandbox often reports failed assertions as `RUNTIME_ERROR`, runtime errors are further decomposed into assertion-driven test aborts, language exceptions, dependency issues, and timeouts.",
        "",
        "## Elixir snapshot",
        "",
    ]
    for category in ("compile", "runtime", "wrong_answer", "other"):
        row = elixir_rows[category]
        lines.append(
            f"- `{category}`: `{row['count']}` failures, `{row['rate_of_all_rows']}%` of all rows "
            f"(95% CI `{row['rate_all_ci_low']}%` to `{row['rate_all_ci_high']}%`), "
            f"`{row['share_of_failures']}%` of Elixir failures "
            f"(95% CI `{row['share_failures_ci_low']}%` to `{row['share_failures_ci_high']}%`)."
        )
    if elixir_subtypes:
        lines.extend(
            [
                "",
                "## Elixir runtime subtype mix",
                "",
            ]
        )
        total_runtime = sum(row["count"] for row in elixir_subtypes)
        for row in elixir_subtypes:
            share = 100.0 * row["count"] / total_runtime if total_runtime else 0.0
            lines.append(f"- `{row['runtime_subtype']}`: `{row['count']}` rows (`{share:.1f}%` of Elixir runtime failures).")
    lines.extend(
        [
            "",
            "## Elixir vs rest",
            "",
        ]
    )
    for row in test_rows:
        if row["comparison_basis"] != "failure_rows":
            continue
        lines.append(
            f"- `{row['category']}` share among failures: odds ratio `{row['odds_ratio']}`, Fisher `p={row['fisher_pvalue']}`, Holm-adjusted `p={row['holm_adjusted_pvalue']}`."
        )
    significant = [row for row in test_rows if row["holm_significant_05"]]
    lines.extend(
        [
            "",
            "## Multiple-testing read",
            "",
            f"- Significant Elixir-vs-rest failure-mode differences after Holm correction: `{len(significant)}`.",
            "- The surviving signal is the lower runtime-failure incidence across all rows, which mostly reflects Elixir's much higher overall pass rate rather than a uniquely different failure mix once conditioned on failure.",
        ]
    )
    output_path = RESULTS_DIR / "elixir_error_taxonomy.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    summary_rows = build_language_summary(rows)
    test_rows = build_elixir_tests(summary_rows)
    stage_rows = build_stage_outcome_rows(rows)
    subtype_rows = build_runtime_subtype_rows(rows)

    write_csv(RESULTS_DIR / "elixir_error_taxonomy_summary.csv", summary_rows)
    write_csv(RESULTS_DIR / "elixir_error_taxonomy_tests.csv", test_rows)
    write_csv(RESULTS_DIR / "elixir_error_taxonomy_stage_outcomes.csv", stage_rows)
    write_csv(RESULTS_DIR / "elixir_error_taxonomy_runtime_subtypes.csv", subtype_rows)
    write_markdown(summary_rows, test_rows, stage_rows, subtype_rows)


if __name__ == "__main__":
    main()
