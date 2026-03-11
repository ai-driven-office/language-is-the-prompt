#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXEC = REPO_ROOT / "outputs" / "openai-5-4-medium-adaptive.native-fixed.exec.jsonl"
DATA_DIR = REPO_ROOT / "data" / "elixir_active_suites"
OUTPUT_DIR = REPO_ROOT / "outputs" / "elixir_active_suites"
RESULTS_DIR = REPO_ROOT / "results" / "elixir_active_suites"
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
MODEL = "gpt-5.4"
LABEL = "GPT-5.4 Medium"
LANGUAGE = "elixir"

SUITE_CONFIG = {
    "suite_a": {
        "title": "Documentation Quality",
        "conditions": ["full_docs", "reference_no_examples", "signature_only", "minimal_docs"],
    },
    "suite_d": {
        "title": "Pattern Matching and Control Flow",
        "conditions": ["baseline", "function_heads", "case_with", "cond_if"],
    },
    "suite_e": {
        "title": "Result Contracts",
        "conditions": ["baseline", "tagged_tuple_helpers", "sentinel_helpers"],
    },
    "suite_f": {
        "title": "Mutability and State Style",
        "conditions": ["baseline", "immutable_pipeline", "explicit_state_threading", "rebinding_stepwise"],
    },
}


def load_source_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def extract_title(question: str) -> str:
    for line in question.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return question.splitlines()[0].strip() if question.strip() else "Untitled"


def extract_first_code_block(question: str) -> str:
    match = re.search(r"```[a-zA-Z0-9_+-]*\n(.*?)```", question, flags=re.S)
    return match.group(1).strip() if match else ""


def strip_sections(question: str, banned_headers: set[str]) -> str:
    lines = question.splitlines()
    output: list[str] = []
    keep = True
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            header = stripped[3:].strip().lower()
            keep = header not in banned_headers
        if keep:
            output.append(line)
    return "\n".join(output).strip()


def keep_only_core_sections(question: str) -> str:
    lines = question.splitlines()
    output: list[str] = []
    allowed = {
        "problem description",
        "class requirements",
        "function specifications",
        "input format",
        "output format",
    }
    keep = True
    seen_header = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            header = stripped[3:].strip().lower()
            keep = header in allowed
            seen_header = True
        if not seen_header and stripped.startswith("#"):
            keep = True
        if keep:
            output.append(line)
    return "\n".join(output).strip()


def build_common_prompt(question_body: str, extra_instruction: str | None = None) -> str:
    parts = [
        "Target language: Elixir.",
        "Return exactly one Markdown code block labeled `elixir` containing the full solution and nothing else.",
        question_body.strip(),
    ]
    if extra_instruction:
        parts.append("Implementation style constraint:")
        parts.append(extra_instruction.strip())
    return "\n\n".join(part for part in parts if part)


def prompt_for_suite_a(row: dict, condition: str) -> str:
    question = row["original_data"]["question"]
    title = extract_title(question)
    signatures = extract_first_code_block(question)
    if condition == "full_docs":
        body = question
    elif condition == "reference_no_examples":
        body = strip_sections(question, {"example usage", "testing", "notes", "constraints"})
    elif condition == "signature_only":
        body = "\n\n".join(
            [
                f"# {title}",
                "Implement the required public API in Elixir and satisfy the hidden tests.",
                "Public API signatures and structures to preserve exactly:",
                f"```elixir\n{signatures}\n```" if signatures else "",
            ]
        ).strip()
    elif condition == "minimal_docs":
        body = "\n\n".join(
            [
                f"# {title}",
                "Implement the required public API in Elixir.",
                "Preserve names, arity, and externally visible behavior expected by the tests.",
                f"```elixir\n{signatures}\n```" if signatures else "",
            ]
        ).strip()
    else:
        raise ValueError(condition)
    return build_common_prompt(body)


def prompt_for_suite_d(row: dict, condition: str) -> str:
    question = keep_only_core_sections(row["original_data"]["question"]) or row["original_data"]["question"]
    instruction = {
        "baseline": None,
        "function_heads": "Prefer multiple function heads, guards, and direct pattern matching in parameters whenever reasonable. Avoid deep nested branching.",
        "case_with": "Prefer explicit `case` and `with` dispatch blocks. Keep branching centralized and readable. Avoid many function heads.",
        "cond_if": "Prefer `cond` and `if` branching with stepwise local bindings. Avoid multiple function heads except where strictly necessary.",
    }[condition]
    return build_common_prompt(question, instruction)


def prompt_for_suite_e(row: dict, condition: str) -> str:
    question = keep_only_core_sections(row["original_data"]["question"]) or row["original_data"]["question"]
    instruction = {
        "baseline": None,
        "tagged_tuple_helpers": "Internally structure helper functions around `{:ok, value}` and `{:error, reason}` results, then normalize the final public return shape to exactly what the task requires.",
        "sentinel_helpers": "Internally structure helper functions around sentinel values such as `nil`, booleans, or fallback defaults instead of tagged tuples, then normalize the final public return shape to exactly what the task requires.",
    }[condition]
    return build_common_prompt(question, instruction)


def prompt_for_suite_f(row: dict, condition: str) -> str:
    question = keep_only_core_sections(row["original_data"]["question"]) or row["original_data"]["question"]
    instruction = {
        "baseline": None,
        "immutable_pipeline": "Prefer recursion, pattern matching, Enum pipelines, and accumulator passing. Avoid stepwise rebinding unless necessary.",
        "explicit_state_threading": "Make every state transition explicit through named accumulators and helper parameters. Favor clarity of state flow over compactness.",
        "rebinding_stepwise": "Use more stepwise local rebinding and branch-local updates to derive the answer. Keep the public API correct, but write the internals in a more stateful style.",
    }[condition]
    return build_common_prompt(question, instruction)


def build_prompt(row: dict, suite_id: str, condition: str) -> str:
    if suite_id == "suite_a":
        return prompt_for_suite_a(row, condition)
    if suite_id == "suite_d":
        return prompt_for_suite_d(row, condition)
    if suite_id == "suite_e":
        return prompt_for_suite_e(row, condition)
    if suite_id == "suite_f":
        return prompt_for_suite_f(row, condition)
    raise ValueError(suite_id)


def select_rows(source_rows: list[dict], per_difficulty: int, seed: int, passed_only: bool) -> list[dict]:
    rng = random.Random(seed)
    eligible = [
        row for row in source_rows
        if row.get("language") == LANGUAGE
        and row.get("original_data", {}).get("difficulty") in {"easy", "medium", "hard"}
    ]
    if passed_only:
        eligible = [row for row in eligible if row.get("success")]
    if per_difficulty <= 0:
        return sorted(eligible, key=lambda row: (row["original_data"]["difficulty"], row["index"]))
    by_difficulty: dict[str, list[dict]] = defaultdict(list)
    for row in eligible:
        by_difficulty[row["original_data"]["difficulty"]].append(row)
    selected: list[dict] = []
    for difficulty in ("easy", "medium", "hard"):
        rows = by_difficulty[difficulty][:]
        rng.shuffle(rows)
        take = rows[:per_difficulty]
        if len(take) < per_difficulty:
            raise RuntimeError(f"Not enough rows for difficulty={difficulty}")
        selected.extend(take)
    return sorted(selected, key=lambda row: (row["original_data"]["difficulty"], row["index"]))


def build_experiment_rows(selected_rows: list[dict]) -> dict[str, list[dict]]:
    outputs: dict[str, list[dict]] = {}
    for suite_id, config in SUITE_CONFIG.items():
        suite_rows: list[dict] = []
        for row in selected_rows:
            original = row["original_data"]
            for condition in config["conditions"]:
                prompt = build_prompt(row, suite_id, condition)
                suite_rows.append(
                    {
                        "experiment_id": f"{suite_id}:{condition}:{row['index']}",
                        "suite_id": suite_id,
                        "suite_title": config["title"],
                        "condition": condition,
                        "source_index": row["index"],
                        "language": LANGUAGE,
                        "difficulty": original["difficulty"],
                        "title": extract_title(original["question"]),
                        "question": prompt,
                        "canonical_solution": original["canonical_solution"],
                        "demo_test_func": original["demo_test_func"],
                        "full_test_func": original["full_test_func"],
                    }
                )
        outputs[suite_id] = suite_rows
    return outputs


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def suite_paths(suite_id: str) -> dict[str, Path]:
    return {
        "input": DATA_DIR / f"{suite_id}.jsonl",
        "output": OUTPUT_DIR / f"{suite_id}.jsonl",
        "exec": OUTPUT_DIR / f"{suite_id}.exec.jsonl",
        "error": OUTPUT_DIR / f"{suite_id}.errors.jsonl",
    }


def suite_counts(suite_id: str) -> dict[str, int]:
    paths = suite_paths(suite_id)
    return {
        "input": count_jsonl(paths["input"]),
        "output": count_jsonl(paths["output"]),
        "exec": count_jsonl(paths["exec"]),
        "error": count_jsonl(paths["error"]),
    }


def suite_is_complete(suite_id: str) -> bool:
    counts = suite_counts(suite_id)
    return counts["input"] > 0 and counts["exec"] == counts["input"]


def write_suite_run_metadata(
    suite_id: str,
    phase: str,
    counts: dict[str, int],
    concurrency: int,
    min_concurrency: int,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "suite_id": suite_id,
        "phase": phase,
        "updated_at_epoch": int(time.time()),
        "model": MODEL,
        "label": LABEL,
        "language": LANGUAGE,
        "concurrency": concurrency,
        "min_concurrency": min_concurrency,
        "counts": counts,
        "complete": counts["input"] > 0 and counts["exec"] == counts["input"],
    }
    (RESULTS_DIR / f"{suite_id}_run_status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generate_inputs(per_difficulty: int, seed: int, passed_only: bool) -> list[Path]:
    source_rows = load_source_rows(SOURCE_EXEC)
    selected_rows = select_rows(source_rows, per_difficulty, seed, passed_only)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    selection_rows = [
        {
            "source_index": row["index"],
            "difficulty": row["original_data"]["difficulty"],
            "title": extract_title(row["original_data"]["question"]),
        }
        for row in selected_rows
    ]
    write_csv(DATA_DIR / "selected_rows.csv", selection_rows)
    manifest = {
        "model": MODEL,
        "label": LABEL,
        "language": LANGUAGE,
        "seed": seed,
        "per_difficulty": per_difficulty,
        "passed_only": passed_only,
        "selected_indices": [row["index"] for row in selected_rows],
        "suite_conditions": {suite_id: config["conditions"] for suite_id, config in SUITE_CONFIG.items()},
    }
    (DATA_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    experiment_sets = build_experiment_rows(selected_rows)
    paths: list[Path] = []
    for suite_id, rows in experiment_sets.items():
        path = DATA_DIR / f"{suite_id}.jsonl"
        write_jsonl(path, rows)
        paths.append(path)
    return paths


def run_cmd(args: list[str]) -> None:
    print("$", " ".join(args))
    subprocess.run(args, check=True, cwd=REPO_ROOT)


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def wilson_interval(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    phat = passed / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    margin = z * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * total)) / total) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def bootstrap_delta_ci(baseline: list[int], condition: list[int], samples: int = 5000, seed: int = 54) -> tuple[float, float]:
    if len(baseline) != len(condition) or not baseline:
        return 0.0, 0.0
    rng = random.Random(seed)
    deltas: list[float] = []
    indices = list(range(len(baseline)))
    for _ in range(samples):
        picks = [rng.choice(indices) for _ in indices]
        base_rate = sum(baseline[idx] for idx in picks) / len(picks)
        cond_rate = sum(condition[idx] for idx in picks) / len(picks)
        deltas.append((cond_rate - base_rate) * 100.0)
    deltas.sort()
    lo = deltas[int(samples * 0.025)]
    hi = deltas[int(samples * 0.975)]
    return round(lo, 1), round(hi, 1)


def exact_binomial_two_sided(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    cumulative = 0.0
    for i in range(0, k + 1):
        cumulative += math.comb(n, i) * (0.5 ** n)
    return min(1.0, 2.0 * cumulative)


def run_suite(suite_id: str, concurrency: int, min_concurrency: int, fresh: bool) -> None:
    paths = suite_paths(suite_id)
    input_path = paths["input"]
    output_path = paths["output"]
    exec_path = paths["exec"]
    error_path = paths["error"]
    python_bin = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
    if fresh:
        for path in (output_path, exec_path, error_path):
            if path.exists():
                path.unlink()
    counts_before = suite_counts(suite_id)
    write_suite_run_metadata(suite_id, "starting", counts_before, concurrency, min_concurrency)
    if counts_before["input"] <= 0:
        raise RuntimeError(f"Input file missing or empty for {suite_id}: {input_path}")
    if counts_before["exec"] == counts_before["input"] and not fresh:
        print(f"Skipping {suite_id}: execution results already complete ({counts_before['exec']}/{counts_before['input']})")
        write_suite_run_metadata(suite_id, "skipped_complete", counts_before, concurrency, min_concurrency)
        return
    run_cmd([str(REPO_ROOT / "scripts" / "start_sandbox.sh")])
    counts_mid = suite_counts(suite_id)
    if counts_mid["output"] < counts_mid["input"] or fresh:
        write_suite_run_metadata(suite_id, "generating", counts_mid, concurrency, min_concurrency)
        run_cmd(
            [
                python_bin,
                str(REPO_ROOT / "scripts" / "api_benchmark_runner.py"),
                "--provider",
                "openai",
                "--model",
                MODEL,
                "--label",
                LABEL,
                "--input-file",
                str(input_path),
                "--output-file",
                str(output_path),
                "--error-file",
                str(error_path),
                "--dedupe-key",
                "experiment_id",
                "--concurrency",
                str(concurrency),
                "--min-concurrency",
                str(min_concurrency),
                "--question-key",
                "question",
                "--reasoning-effort",
                "medium",
                "--verbosity",
                "low",
                "--max-tokens",
                "4096",
                "--max-attempts",
                "4",
            ]
        )
    else:
        print(f"Skipping generation for {suite_id}: outputs already complete ({counts_mid['output']}/{counts_mid['input']})")
    counts_pre_exec = suite_counts(suite_id)
    write_suite_run_metadata(suite_id, "scoring", counts_pre_exec, concurrency, min_concurrency)
    run_cmd(
        [
            python_bin,
            str(REPO_ROOT / "call_sandbox.py"),
            "--input_file",
            str(output_path),
            "--output",
            str(exec_path),
            "--server_ip",
            "localhost",
            "--server_port",
            "8080",
            "--concurrency",
            str(max(concurrency, 8)),
            "--native-langs",
            "elixir",
            "--solution_key",
            "output",
        ]
    )
    write_suite_run_metadata(suite_id, "complete", suite_counts(suite_id), concurrency, min_concurrency)


def summarize_suite(suite_id: str) -> dict:
    exec_path = OUTPUT_DIR / f"{suite_id}.exec.jsonl"
    input_path = DATA_DIR / f"{suite_id}.jsonl"
    input_rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    exec_rows = [json.loads(line) for line in exec_path.read_text(encoding="utf-8").splitlines() if line.strip()] if exec_path.exists() else []
    exec_by_id = {row["original_data"]["experiment_id"]: row for row in exec_rows}
    missing_rows: list[dict] = []
    rows: list[dict] = []
    for input_row in input_rows:
        experiment_id = input_row["experiment_id"]
        row = exec_by_id.get(experiment_id)
        if row is None:
            row = {
                "success": False,
                "demo_test_result": "MISSING_GENERATION",
                "full_test_result": "MISSING_GENERATION",
                "original_data": input_row,
            }
            missing_rows.append(
                {
                    "experiment_id": experiment_id,
                    "suite_id": suite_id,
                    "condition": input_row["condition"],
                    "source_index": input_row["source_index"],
                    "difficulty": input_row["difficulty"],
                    "title": input_row["title"],
                }
            )
        rows.append(row)
    by_condition: dict[str, list[dict]] = defaultdict(list)
    by_condition_difficulty: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        original = row["original_data"]
        condition = original["condition"]
        difficulty = original["difficulty"]
        by_condition[condition].append(row)
        by_condition_difficulty[(condition, difficulty)].append(row)

    summary_rows: list[dict] = []
    paired_rows: list[dict] = []
    baseline_rate = None
    baseline_successes: dict[int, int] = {}
    if "baseline" in by_condition:
        baseline = by_condition["baseline"]
        baseline_rate = sum(1 for row in baseline if row["success"]) / len(baseline)
        baseline_successes = {row["original_data"]["source_index"]: int(row["success"]) for row in baseline}
    elif "full_docs" in by_condition:
        baseline = by_condition["full_docs"]
        baseline_rate = sum(1 for row in baseline if row["success"]) / len(baseline)
        baseline_successes = {row["original_data"]["source_index"]: int(row["success"]) for row in baseline}
    for condition, condition_rows in sorted(by_condition.items()):
        passed = sum(1 for row in condition_rows if row["success"])
        total = len(condition_rows)
        rate = passed / total if total else 0.0
        ci_low, ci_high = wilson_interval(passed, total)
        summary_rows.append(
            {
                "suite_id": suite_id,
                "condition": condition,
                "passed": passed,
                "total": total,
                "pass_rate": round(rate * 100.0, 1),
                "ci_low": round(ci_low * 100.0, 1),
                "ci_high": round(ci_high * 100.0, 1),
                "delta_vs_baseline": round(((rate - baseline_rate) * 100.0), 1) if baseline_rate is not None else 0.0,
            }
        )
        if condition in {"baseline", "full_docs"}:
            continue
        condition_successes = {row["original_data"]["source_index"]: int(row["success"]) for row in condition_rows}
        shared = sorted(set(baseline_successes) & set(condition_successes))
        baseline_vector = [baseline_successes[idx] for idx in shared]
        condition_vector = [condition_successes[idx] for idx in shared]
        b = sum(1 for base, cond in zip(baseline_vector, condition_vector) if base == 1 and cond == 0)
        c = sum(1 for base, cond in zip(baseline_vector, condition_vector) if base == 0 and cond == 1)
        baseline_pass_subset = [cond for base, cond in zip(baseline_vector, condition_vector) if base == 1]
        baseline_fail_subset = [cond for base, cond in zip(baseline_vector, condition_vector) if base == 0]
        ci_delta_low, ci_delta_high = bootstrap_delta_ci(baseline_vector, condition_vector)
        paired_rows.append(
            {
                "suite_id": suite_id,
                "baseline_condition": "baseline" if "baseline" in by_condition else "full_docs",
                "condition": condition,
                "n_shared": len(shared),
                "baseline_only_wins": b,
                "condition_only_wins": c,
                "mcnemar_pvalue": round(exact_binomial_two_sided(b, c), 6),
                "delta_ci_low": ci_delta_low,
                "delta_ci_high": ci_delta_high,
                "baseline_pass_subset_n": len(baseline_pass_subset),
                "condition_pass_rate_on_baseline_pass_subset": round(
                    (sum(baseline_pass_subset) / len(baseline_pass_subset) * 100.0) if baseline_pass_subset else 0.0,
                    1,
                ),
                "baseline_fail_subset_n": len(baseline_fail_subset),
                "condition_pass_rate_on_baseline_fail_subset": round(
                    (sum(baseline_fail_subset) / len(baseline_fail_subset) * 100.0) if baseline_fail_subset else 0.0,
                    1,
                ),
            }
        )
    detail_rows: list[dict] = []
    task_comparison_rows: list[dict] = []
    for (condition, difficulty), condition_rows in sorted(by_condition_difficulty.items()):
        passed = sum(1 for row in condition_rows if row["success"])
        total = len(condition_rows)
        detail_rows.append(
            {
                "suite_id": suite_id,
                "condition": condition,
                "difficulty": difficulty,
                "passed": passed,
                "total": total,
                "pass_rate": round((passed / total if total else 0.0) * 100.0, 1),
            }
        )
    baseline_condition = "baseline" if "baseline" in by_condition else "full_docs"
    if baseline_successes:
        baseline_rows = {row["original_data"]["source_index"]: row for row in by_condition[baseline_condition]}
        for condition, condition_rows in sorted(by_condition.items()):
            if condition == baseline_condition:
                continue
            condition_map = {row["original_data"]["source_index"]: row for row in condition_rows}
            shared = sorted(set(baseline_rows) & set(condition_map))
            for source_index in shared:
                base_row = baseline_rows[source_index]
                cond_row = condition_map[source_index]
                base_success = int(base_row["success"])
                cond_success = int(cond_row["success"])
                if base_success == cond_success:
                    outcome = "same"
                elif base_success and not cond_success:
                    outcome = "baseline_only"
                else:
                    outcome = "condition_only"
                task_comparison_rows.append(
                    {
                        "suite_id": suite_id,
                        "baseline_condition": baseline_condition,
                        "condition": condition,
                        "source_index": source_index,
                        "difficulty": cond_row["original_data"]["difficulty"],
                        "title": cond_row["original_data"]["title"],
                        "baseline_success": base_success,
                        "condition_success": cond_success,
                        "outcome": outcome,
                    }
                )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS_DIR / f"{suite_id}_summary.csv", summary_rows)
    write_csv(RESULTS_DIR / f"{suite_id}_by_difficulty.csv", detail_rows)
    if paired_rows:
        write_csv(RESULTS_DIR / f"{suite_id}_paired_stats.csv", paired_rows)
    if task_comparison_rows:
        write_csv(RESULTS_DIR / f"{suite_id}_task_comparisons.csv", task_comparison_rows)
    if missing_rows:
        write_csv(RESULTS_DIR / f"{suite_id}_missing_generations.csv", missing_rows)
    lines = [
        f"# {suite_id} Active Ablation Summary",
        "",
        f"Active ablation rerun using `{MODEL}` / medium reasoning on `{LANGUAGE}` tasks.",
        "",
        "## Condition summary",
        "",
        "| Condition | Passed | Total | Pass Rate | 95% CI | Delta vs Baseline |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['condition']} | {row['passed']} | {row['total']} | {row['pass_rate']}% | {row['ci_low']}% to {row['ci_high']}% | {row['delta_vs_baseline']:+.1f} |"
        )
    if paired_rows:
        lines.extend(
            [
                "",
                "## Paired comparison vs baseline",
                "",
                "| Condition | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset | Cond. Pass Rate on Baseline-Fail Subset |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in paired_rows:
            lines.append(
                f"| {row['condition']} | {row['baseline_only_wins']} | {row['condition_only_wins']} | {row['mcnemar_pvalue']} | "
                f"{row['delta_ci_low']} to {row['delta_ci_high']} | {row['condition_pass_rate_on_baseline_pass_subset']}% | "
                f"{row['condition_pass_rate_on_baseline_fail_subset']}% |"
            )
    if missing_rows:
        lines.extend(
            [
                "",
                "## Missing generations",
                "",
                f"- Missing generations counted as failures: `{len(missing_rows)}`",
            ]
        )
    lines.extend(
        [
            "",
            "## By difficulty",
            "",
            "| Condition | Difficulty | Passed | Total | Pass Rate |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in detail_rows:
        lines.append(
            f"| {row['condition']} | {row['difficulty']} | {row['passed']} | {row['total']} | {row['pass_rate']}% |"
        )
    (RESULTS_DIR / f"{suite_id}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"summary": summary_rows, "detail": detail_rows, "paired": paired_rows}


def summarize_all() -> None:
    combined: list[dict] = []
    key_findings: list[str] = []
    for suite_id in SUITE_CONFIG:
        exec_path = OUTPUT_DIR / f"{suite_id}.exec.jsonl"
        if not exec_path.exists():
            continue
        payload = summarize_suite(suite_id)
        summary_rows = payload["summary"]
        baseline_condition = "baseline" if any(row["condition"] == "baseline" for row in summary_rows) else "full_docs"
        baseline = next(row for row in summary_rows if row["condition"] == baseline_condition)
        best = max(summary_rows, key=lambda row: row["pass_rate"])
        worst = min(summary_rows, key=lambda row: row["pass_rate"])
        combined.extend(summary_rows)
        key_findings.append(
            f"- `{suite_id}`: baseline `{baseline['condition']}` = `{baseline['pass_rate']}%`; best condition `{best['condition']}` = `{best['pass_rate']}%`; worst condition `{worst['condition']}` = `{worst['pass_rate']}%`."
        )
    write_csv(RESULTS_DIR / "combined_summary.csv", combined)
    lines = [
        "# Elixir Active Ablation Study",
        "",
        "This report summarizes the active rerun results for the scientific Elixir suites.",
        "",
        "## Key findings",
        "",
    ]
    lines.extend(key_findings)
    (RESULTS_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "run", "summarize", "all"])
    parser.add_argument("--suite", choices=["all", *SUITE_CONFIG.keys()], default="all")
    parser.add_argument("--per-difficulty", type=int, default=3)
    parser.add_argument("--seed", type=int, default=54)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--min-concurrency", type=int, default=8)
    parser.add_argument("--passed-only", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command in {"generate", "all"}:
        generate_inputs(args.per_difficulty, args.seed, args.passed_only)
    if args.command in {"run", "all"}:
        suite_ids = list(SUITE_CONFIG.keys()) if args.suite == "all" else [args.suite]
        for suite_id in suite_ids:
            run_suite(suite_id, args.concurrency, args.min_concurrency, args.fresh)
    if args.command in {"summarize", "all"}:
        summarize_all()


if __name__ == "__main__":
    main()
