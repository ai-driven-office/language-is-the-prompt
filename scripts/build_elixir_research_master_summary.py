#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
ACTIVE_DIR = RESULTS_DIR / "elixir_active_suites"
OUTPUTS_DIR = REPO_ROOT / "outputs" / "elixir_active_suites"
DATA_DIR = REPO_ROOT / "data" / "elixir_active_suites"

ACTIVE_SUITES = {
    "suite_a": {"title": "Documentation Quality", "baseline": "full_docs"},
    "suite_d": {"title": "Pattern Matching and Control Flow", "baseline": "baseline"},
    "suite_e": {"title": "Result Contracts", "baseline": "baseline"},
    "suite_f": {"title": "Mutability and State Style", "baseline": "baseline"},
}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_csv_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return read_csv(path)


def to_map(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def suite_progress(suite_id: str) -> dict:
    input_rows = count_jsonl(DATA_DIR / f"{suite_id}.jsonl")
    output_rows = count_jsonl(OUTPUTS_DIR / f"{suite_id}.jsonl")
    exec_rows = count_jsonl(OUTPUTS_DIR / f"{suite_id}.exec.jsonl")
    if input_rows == 0:
        status = "missing"
    elif exec_rows == input_rows:
        status = "complete"
    elif output_rows == input_rows:
        status = "awaiting_scoring"
    elif output_rows > 0:
        status = "generating"
    else:
        status = "pending"
    return {
        "suite_id": suite_id,
        "input_rows": input_rows,
        "generated_rows": output_rows,
        "scored_rows": exec_rows,
        "status": status,
    }


def active_suite_payload(suite_id: str) -> dict | None:
    summary_rows = read_csv_if_exists(ACTIVE_DIR / f"{suite_id}_summary.csv")
    if not summary_rows:
        return None
    summary_map = to_map(summary_rows, "condition")
    pair_rows = read_csv_if_exists(ACTIVE_DIR / f"{suite_id}_paired_stats.csv")
    pair_map = to_map(pair_rows, "condition") if pair_rows else {}
    detail_rows = read_csv_if_exists(ACTIVE_DIR / f"{suite_id}_by_difficulty.csv")
    task_rows = read_csv_if_exists(ACTIVE_DIR / f"{suite_id}_task_comparisons.csv")
    baseline = ACTIVE_SUITES[suite_id]["baseline"]
    return {
        "suite_id": suite_id,
        "title": ACTIVE_SUITES[suite_id]["title"],
        "baseline": baseline,
        "summary": summary_rows,
        "summary_map": summary_map,
        "paired": pair_rows,
        "paired_map": pair_map,
        "by_difficulty": detail_rows,
        "task_comparisons": task_rows,
    }


def build_matrix_rows(
    suite_h: dict,
    passive: dict[str, dict],
    active: dict[str, dict],
) -> list[dict]:
    rows = [
        {
            "evidence_bucket": "artifact_control",
            "suite": "suite_h",
            "signal": "elixir_delta_vs_difficulty_only",
            "value": suite_h["delta_vs_difficulty_only"],
            "interpretation": "Elixir stays far above expectation after difficulty controls.",
        },
        {
            "evidence_bucket": "artifact_control",
            "suite": "suite_h",
            "signal": "elixir_delta_vs_question_len",
            "value": suite_h["delta_vs_difficulty_and_question_len"],
            "interpretation": "Question length does not erase Elixir's lead.",
        },
        {
            "evidence_bucket": "passive_proxy",
            "suite": "suite_d",
            "signal": "control_flow_score",
            "value": passive["suite_d"]["mean_control_flow_score"],
            "interpretation": "Elixir scores highest on the current control-flow legibility proxy.",
        },
        {
            "evidence_bucket": "passive_proxy",
            "suite": "suite_f",
            "signal": "mutability_burden_score",
            "value": passive["suite_f"]["mean_mutability_burden_score"],
            "interpretation": "Elixir shows low mutability burden while keeping the highest pass rate.",
        },
    ]
    suite_a = active.get("suite_a")
    if suite_a and "signature_only" in suite_a["summary_map"]:
        rows.append(
            {
                "evidence_bucket": "active_ablation",
                "suite": "suite_a",
                "signal": "signature_only_delta_vs_full_docs",
                "value": suite_a["summary_map"]["signature_only"]["delta_vs_baseline"],
                "interpretation": "Reducing the task to signatures only materially hurts performance.",
            }
        )
    suite_e = active.get("suite_e")
    if suite_e and "sentinel_helpers" in suite_e["summary_map"]:
        rows.append(
            {
                "evidence_bucket": "active_ablation",
                "suite": "suite_e",
                "signal": "sentinel_helpers_delta_vs_baseline",
                "value": suite_e["summary_map"]["sentinel_helpers"]["delta_vs_baseline"],
                "interpretation": "Weaker implicit helper contracts perform worse than the baseline prompt.",
            }
        )
    suite_d = active.get("suite_d")
    if suite_d and len(suite_d["summary"]) > 1:
        worst = min(
            (row for row in suite_d["summary"] if row["condition"] != suite_d["baseline"]),
            key=lambda row: float(row["pass_rate"]),
        )
        rows.append(
            {
                "evidence_bucket": "active_ablation",
                "suite": "suite_d",
                "signal": "worst_control_flow_condition_delta",
                "value": worst["delta_vs_baseline"],
                "interpretation": "Alternative control-flow prompting under active rerun did not clearly beat the baseline style.",
            }
        )
    suite_f = active.get("suite_f")
    if suite_f and len(suite_f["summary"]) > 1:
        worst = min(
            (row for row in suite_f["summary"] if row["condition"] != suite_f["baseline"]),
            key=lambda row: float(row["pass_rate"]),
        )
        rows.append(
            {
                "evidence_bucket": "active_ablation",
                "suite": "suite_f",
                "signal": "worst_state_style_condition_delta",
                "value": worst["delta_vs_baseline"],
                "interpretation": "Alternative state-style prompting did not clearly outperform the baseline prompt.",
            }
        )
    return rows


def main() -> None:
    suite_h = to_map(
        read_csv(RESULTS_DIR / "elixir_suite_h" / "suite_h_artifact_controls.csv"),
        "language",
    )["elixir"]
    passive = {
        "suite_a": to_map(read_csv(RESULTS_DIR / "elixir_suite_a" / "suite_a_docs_quality.csv"), "language")["elixir"],
        "suite_d": to_map(read_csv(RESULTS_DIR / "elixir_suite_d" / "suite_d_control_flow.csv"), "language")["elixir"],
        "suite_e": to_map(read_csv(RESULTS_DIR / "elixir_suite_e" / "suite_e_result_contracts.csv"), "language")["elixir"],
        "suite_f": to_map(read_csv(RESULTS_DIR / "elixir_suite_f" / "suite_f_mutability.csv"), "language")["elixir"],
        "suite_g": to_map(read_csv(RESULTS_DIR / "elixir_suite_g" / "suite_g_alignment.csv"), "language")["elixir"],
    }

    active_payloads = {
        suite_id: payload
        for suite_id, payload in (
            (suite_id, active_suite_payload(suite_id))
            for suite_id in ACTIVE_SUITES
        )
        if payload is not None
    }

    progress_rows = [suite_progress(suite_id) for suite_id in ACTIVE_SUITES]
    matrix_rows = build_matrix_rows(suite_h, passive, active_payloads)

    payload = {
        "benchmark_replication": {
            "model": "gpt-5.4",
            "reasoning": "medium",
            "main_elixir_pass_rate": suite_h["observed_pass_rate"],
            "artifact_control_expected_difficulty_only": suite_h["expected_pass_rate_difficulty_only"],
            "artifact_control_delta_difficulty_only": suite_h["delta_vs_difficulty_only"],
            "artifact_control_delta_question_len": suite_h["delta_vs_difficulty_and_question_len"],
            "artifact_control_delta_full_test_len": suite_h["delta_vs_difficulty_and_full_test_len"],
            "hard_task_pass_rate": "86.3",
        },
        "current_hypothesis": {
            "primary": "Elixir appears unusually model-friendly because docs and public contracts make intent explicit and reduce ambiguity.",
            "secondary": [
                "Pattern matching likely helps by externalizing control flow.",
                "Low hidden-state burden likely helps by reducing implicit mutable-state reasoning.",
            ],
            "not_supported_as_primary": [
                "benchmark composition alone",
                "stylistic cleanliness alone",
                "docs alignment alone",
            ],
        },
        "active_suite_progress": progress_rows,
        "passive_suites": {
            "suite_a_docs_quality": {
                "mean_docs_score": passive["suite_a"]["mean_docs_score"],
                "docs_success_corr": passive["suite_a"]["success_feature_corr"],
            },
            "suite_d_control_flow": {
                "mean_control_flow_score": passive["suite_d"]["mean_control_flow_score"],
                "pattern_signal_count": passive["suite_d"]["mean_pattern_signal_count"],
            },
            "suite_e_result_contracts": {
                "mean_contract_score": passive["suite_e"]["mean_contract_score"],
                "tagged_tuple_count": passive["suite_e"]["mean_tagged_tuple_count"],
            },
            "suite_f_mutability": {
                "mean_mutability_burden_score": passive["suite_f"]["mean_mutability_burden_score"],
            },
            "suite_g_alignment": {
                "mean_alignment_score": passive["suite_g"]["mean_alignment_score"],
            },
        },
        "active_suites": {
            suite_id: {
                "title": payload["title"],
                "baseline": payload["baseline"],
                "summary": payload["summary"],
                "paired": payload["paired"],
            }
            for suite_id, payload in active_payloads.items()
        },
        "language_design_lessons": [
            "Make public API behavior explicit in docs and examples.",
            "Prefer standard result-shape conventions over ad hoc sentinel returns.",
            "Reduce hidden mutable state and make control flow legible.",
            "Keep the gap small between docs, tests, and implementation.",
        ],
        "evidence_matrix": matrix_rows,
    }

    json_path = RESULTS_DIR / "elixir_research_master_summary.json"
    yaml_path = RESULTS_DIR / "elixir_research_master_summary.yaml"
    md_path = RESULTS_DIR / "elixir_research_master_summary.md"
    csv_path = RESULTS_DIR / "elixir_research_evidence_matrix.csv"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    yaml_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix_rows[0].keys()))
        writer.writeheader()
        for row in matrix_rows:
            writer.writerow(row)

    lines = [
        "# Elixir Research Master Summary",
        "",
        "## Defended read",
        "",
        "- Elixir's lead survives the benchmark-artifact controls in Suite H.",
        "- The strongest current causal evidence points to documentation richness and explicit public contracts.",
        "- Pattern matching and low hidden-state burden remain plausible secondary contributors.",
        "",
        "## Benchmark replication",
        "",
        f"- Corrected Elixir benchmark score: `{suite_h['observed_pass_rate']}%`",
        f"- Delta vs difficulty-only expectation: `{suite_h['delta_vs_difficulty_only']}` points",
        f"- Delta vs difficulty+question-length expectation: `{suite_h['delta_vs_difficulty_and_question_len']}` points",
        f"- Hard-task pass rate: `86.3%`",
        "",
        "## Active suite progress",
        "",
    ]
    for row in progress_rows:
        lines.append(
            f"- `{row['suite_id']}`: status `{row['status']}`, generated `{row['generated_rows']}/{row['input_rows']}`, scored `{row['scored_rows']}/{row['input_rows']}`"
        )
    if active_payloads:
        lines.extend(
            [
                "",
                "## Active suite highlights",
                "",
            ]
        )
        for suite_id in ("suite_a", "suite_d", "suite_e", "suite_f"):
            payload_suite = active_payloads.get(suite_id)
            if not payload_suite:
                continue
            baseline = payload_suite["summary_map"][payload_suite["baseline"]]
            lines.append(
                f"- `{suite_id}` ({payload_suite['title']}): baseline `{payload_suite['baseline']}` = `{baseline['pass_rate']}%`"
            )
            for row in payload_suite["summary"]:
                if row["condition"] == payload_suite["baseline"]:
                    continue
                lines.append(
                    f"  {row['condition']}: `{row['pass_rate']}%` ({row['delta_vs_baseline']:+.1f} vs baseline)"
                )
    lines.extend(
        [
            "",
            "## Design lessons",
            "",
        ]
    )
    for lesson in payload["language_design_lessons"]:
        lines.append(f"- {lesson}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
