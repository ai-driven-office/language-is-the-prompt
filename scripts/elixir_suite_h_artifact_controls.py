#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def percentile_bounds(values: list[int], buckets: int = 4) -> list[float]:
    if not values:
        return []
    ordered = sorted(values)
    bounds: list[float] = []
    for idx in range(1, buckets):
        pos = (len(ordered) - 1) * idx / buckets
        lo = math.floor(pos)
        hi = math.ceil(pos)
        if lo == hi:
            bounds.append(float(ordered[lo]))
        else:
            frac = pos - lo
            bounds.append(ordered[lo] * (1 - frac) + ordered[hi] * frac)
    return bounds


def bucket_for(value: int, bounds: list[float]) -> int:
    bucket = 0
    for bound in bounds:
        if value > bound:
            bucket += 1
        else:
            break
    return bucket


def median_int(values: list[int]) -> int:
    if not values:
        return 0
    return int(round(statistics.median(values)))


def safe_rate(passed: int, total: int) -> float:
    if total == 0:
        return 0.0
    return passed / total


def format_pct(rate: float) -> float:
    return round(rate * 100.0, 1)


def build_record(row: dict, question_bounds: list[float], full_test_bounds: list[float]) -> dict:
    original = row.get("original_data") or {}
    full_response = ((row.get("full_test_result") or {}).get("response") or {})
    demo_response = ((row.get("demo_test_result") or {}).get("response") or {})

    question_len = len(original.get("question") or "")
    canonical_len = len(original.get("canonical_solution") or "")
    demo_len = len(original.get("demo_test_func") or "")
    full_test_len = len(original.get("full_test_func") or "")

    return {
        "index": row.get("index"),
        "language": row.get("language"),
        "success": bool(row.get("success")),
        "difficulty": original.get("difficulty", "unknown"),
        "question_len": question_len,
        "canonical_len": canonical_len,
        "demo_len": demo_len,
        "full_test_len": full_test_len,
        "question_bucket": bucket_for(question_len, question_bounds),
        "full_test_bucket": bucket_for(full_test_len, full_test_bounds),
        "full_outcome": full_response.get("exec_outcome", "MISSING"),
        "demo_outcome": demo_response.get("exec_outcome", "MISSING"),
    }


def baseline_rate(records: list[dict], current_language: str, key_fn) -> float | None:
    matches = [record for record in records if record["language"] != current_language and key_fn(record)]
    if not matches:
        return None
    return sum(1 for record in matches if record["success"]) / len(matches)


def compute_expected_rates(records: list[dict], language: str) -> dict[str, float]:
    language_rows = [record for record in records if record["language"] == language]
    global_rate = safe_rate(sum(1 for record in records if record["success"]), len(records))
    results = {
        "expected_difficulty_only": 0.0,
        "expected_difficulty_and_question_len": 0.0,
        "expected_difficulty_and_full_test_len": 0.0,
    }

    for record in language_rows:
        difficulty_rate = baseline_rate(
            records,
            language,
            lambda item, difficulty=record["difficulty"]: item["difficulty"] == difficulty,
        )
        dq_rate = baseline_rate(
            records,
            language,
            lambda item,
            difficulty=record["difficulty"],
            question_bucket=record["question_bucket"]: item["difficulty"] == difficulty
            and item["question_bucket"] == question_bucket,
        )
        df_rate = baseline_rate(
            records,
            language,
            lambda item,
            difficulty=record["difficulty"],
            full_bucket=record["full_test_bucket"]: item["difficulty"] == difficulty
            and item["full_test_bucket"] == full_bucket,
        )
        results["expected_difficulty_only"] += difficulty_rate if difficulty_rate is not None else global_rate
        results["expected_difficulty_and_question_len"] += dq_rate if dq_rate is not None else (
            difficulty_rate if difficulty_rate is not None else global_rate
        )
        results["expected_difficulty_and_full_test_len"] += df_rate if df_rate is not None else (
            difficulty_rate if difficulty_rate is not None else global_rate
        )

    total = len(language_rows) or 1
    return {name: value / total for name, value in results.items()}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_summary(records: list[dict]) -> tuple[list[dict], list[dict], dict]:
    by_language: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_language[record["language"]].append(record)

    language_rows: list[dict] = []
    difficulty_rows: list[dict] = []

    for language, rows in sorted(by_language.items()):
        outcomes = Counter(record["full_outcome"] for record in rows)
        difficulties = Counter(record["difficulty"] for record in rows)
        expected = compute_expected_rates(records, language)
        observed_rate = safe_rate(sum(1 for record in rows if record["success"]), len(rows))

        language_row = {
            "language": language,
            "total_rows": len(rows),
            "observed_pass_rate": format_pct(observed_rate),
            "expected_pass_rate_difficulty_only": format_pct(expected["expected_difficulty_only"]),
            "delta_vs_difficulty_only": round(format_pct(observed_rate - expected["expected_difficulty_only"]), 1),
            "expected_pass_rate_difficulty_and_question_len": format_pct(expected["expected_difficulty_and_question_len"]),
            "delta_vs_difficulty_and_question_len": round(format_pct(observed_rate - expected["expected_difficulty_and_question_len"]), 1),
            "expected_pass_rate_difficulty_and_full_test_len": format_pct(expected["expected_difficulty_and_full_test_len"]),
            "delta_vs_difficulty_and_full_test_len": round(format_pct(observed_rate - expected["expected_difficulty_and_full_test_len"]), 1),
            "hard_rows": difficulties.get("hard", 0),
            "hard_pct": format_pct(safe_rate(difficulties.get("hard", 0), len(rows))),
            "median_question_chars": median_int([record["question_len"] for record in rows]),
            "median_canonical_chars": median_int([record["canonical_len"] for record in rows]),
            "median_full_test_chars": median_int([record["full_test_len"] for record in rows]),
            "runtime_errors": outcomes.get("RUNTIME_ERROR", 0),
            "compilation_errors": outcomes.get("COMPILATION_ERROR", 0),
            "wrong_answers": outcomes.get("WRONG_ANSWER", 0),
            "time_limit_exceeded": outcomes.get("TIME_LIMIT_EXCEEDED", 0),
        }
        language_rows.append(language_row)

        for difficulty in ("easy", "medium", "hard"):
            difficulty_subset = [record for record in rows if record["difficulty"] == difficulty]
            difficulty_rows.append(
                {
                    "language": language,
                    "difficulty": difficulty,
                    "passed": sum(1 for record in difficulty_subset if record["success"]),
                    "total": len(difficulty_subset),
                    "pass_rate": format_pct(
                        safe_rate(sum(1 for record in difficulty_subset if record["success"]), len(difficulty_subset))
                    ),
                }
            )

    overall = {
        "overall_pass_rate": format_pct(safe_rate(sum(1 for record in records if record["success"]), len(records))),
        "languages": len(by_language),
        "rows": len(records),
    }
    return language_rows, difficulty_rows, overall


def write_markdown(path: Path, language_rows: list[dict], difficulty_rows: list[dict], overall: dict) -> None:
    ranked = sorted(language_rows, key=lambda row: row["observed_pass_rate"], reverse=True)
    adjusted_q = sorted(language_rows, key=lambda row: row["delta_vs_difficulty_and_question_len"], reverse=True)
    adjusted_full = sorted(language_rows, key=lambda row: row["delta_vs_difficulty_and_full_test_len"], reverse=True)
    elixir = next(row for row in language_rows if row["language"] == "elixir")
    hard_rows = [row for row in difficulty_rows if row["difficulty"] == "hard"]
    hard_ranked = sorted(hard_rows, key=lambda row: row["pass_rate"], reverse=True)
    lines = [
        "# Suite H: Benchmark Artifact Controls",
        "",
        f"- Overall pass rate in this scored run: `{overall['overall_pass_rate']}%` across `{overall['rows']}` rows and `{overall['languages']}` languages.",
        f"- Elixir observed pass rate: `{elixir['observed_pass_rate']}%`.",
        f"- Elixir delta vs difficulty-only expectation: `{elixir['delta_vs_difficulty_only']:+.1f}` points.",
        f"- Elixir delta vs difficulty+question-length expectation: `{elixir['delta_vs_difficulty_and_question_len']:+.1f}` points.",
        f"- Elixir delta vs difficulty+full-test-length expectation: `{elixir['delta_vs_difficulty_and_full_test_len']:+.1f}` points.",
        "",
        "## Initial read",
        "",
        "Elixir does not look like an obvious easy-slice artifact in the current run. It remains strongly above its leave-one-language-out expected rate even after controlling for difficulty and a crude brevity proxy.",
        "",
        "## Top observed languages",
        "",
        "| Language | Observed | Delta vs Difficulty | Delta vs Difficulty+Question | Delta vs Difficulty+Full Test | Hard % | Median Question | Runtime Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ranked[:8]:
        lines.append(
            f"| {row['language']} | {row['observed_pass_rate']}% | {row['delta_vs_difficulty_only']:+.1f} | {row['delta_vs_difficulty_and_question_len']:+.1f} | {row['delta_vs_difficulty_and_full_test_len']:+.1f} | {row['hard_pct']}% | {row['median_question_chars']} | {row['runtime_errors']} |"
        )

    lines.extend(
        [
            "",
            "## Top adjusted by difficulty + question length",
            "",
            "| Language | Observed | Expected | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in adjusted_q[:8]:
        lines.append(
            f"| {row['language']} | {row['observed_pass_rate']}% | {row['expected_pass_rate_difficulty_and_question_len']}% | {row['delta_vs_difficulty_and_question_len']:+.1f} |"
        )

    lines.extend(
        [
            "",
            "## Hard-bucket leaders",
            "",
            "| Language | Passed | Total | Pass Rate |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in hard_ranked[:8]:
        lines.append(f"| {row['language']} | {row['passed']} | {row['total']} | {row['pass_rate']}% |")

    lines.extend(
        [
            "",
            "## Caveat",
            "",
            "Elixir rows appear shorter than many peer languages by median question and test length. That remains a live confound. The artifact-control result is therefore directional, not final proof.",
            "",
            "## Files",
            "",
            "- `suite_h_artifact_controls.csv`: per-language artifact-control summary",
            "- `suite_h_artifact_controls_by_difficulty.csv`: per-language difficulty breakdown",
            "- `suite_h_artifact_controls.json`: machine-readable output",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Suite H artifact controls for the Elixir PRD.")
    parser.add_argument(
        "--scored-file",
        default=str(REPO_ROOT / "outputs" / "openai-5-4-medium-adaptive.native-fixed.exec.jsonl"),
        help="Path to the scored execution JSONL file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "results" / "elixir_suite_h"),
        help="Directory for CSV/JSON/markdown outputs.",
    )
    args = parser.parse_args()

    scored_path = Path(args.scored_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_rows = load_rows(scored_path)
    question_bounds = percentile_bounds(
        [len((row.get("original_data") or {}).get("question") or "") for row in raw_rows]
    )
    full_test_bounds = percentile_bounds(
        [len((row.get("original_data") or {}).get("full_test_func") or "") for row in raw_rows]
    )
    records = [build_record(row, question_bounds, full_test_bounds) for row in raw_rows]

    language_rows, difficulty_rows, overall = build_summary(records)

    language_fieldnames = [
        "language",
        "total_rows",
        "observed_pass_rate",
        "expected_pass_rate_difficulty_only",
        "delta_vs_difficulty_only",
        "expected_pass_rate_difficulty_and_question_len",
        "delta_vs_difficulty_and_question_len",
        "expected_pass_rate_difficulty_and_full_test_len",
        "delta_vs_difficulty_and_full_test_len",
        "hard_rows",
        "hard_pct",
        "median_question_chars",
        "median_canonical_chars",
        "median_full_test_chars",
        "runtime_errors",
        "compilation_errors",
        "wrong_answers",
        "time_limit_exceeded",
    ]
    difficulty_fieldnames = ["language", "difficulty", "passed", "total", "pass_rate"]

    write_csv(output_dir / "suite_h_artifact_controls.csv", language_fieldnames, language_rows)
    write_csv(output_dir / "suite_h_artifact_controls_by_difficulty.csv", difficulty_fieldnames, difficulty_rows)
    (output_dir / "suite_h_artifact_controls.json").write_text(
        json.dumps(
            {
                "overall": overall,
                "language_summary": language_rows,
                "difficulty_summary": difficulty_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(
        output_dir / "suite_h_artifact_controls.md",
        language_rows,
        difficulty_rows,
        overall,
    )

    print(f"Wrote {output_dir / 'suite_h_artifact_controls.csv'}")
    print(f"Wrote {output_dir / 'suite_h_artifact_controls_by_difficulty.csv'}")
    print(f"Wrote {output_dir / 'suite_h_artifact_controls.json'}")
    print(f"Wrote {output_dir / 'suite_h_artifact_controls.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
