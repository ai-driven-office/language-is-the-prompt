#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from build_explicit_task_panel_benchmark import (
    build_implementations,
    language_note,
    return_contract_note,
    write_csv,
    write_jsonl,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY_DIR = REPO_ROOT / "studies" / "explicit_task_factorial"
GENERATED_DIR = STUDY_DIR / "generated"
DATA_DIR = REPO_ROOT / "data" / "explicit_task_factorial"


def augment_question(question: str, task_id: str, language: str, row: dict[str, Any]) -> str:
    factor_levels = row["factor_levels"]
    lines = [
        question.strip(),
        "",
        "## Implementation Notes",
        f"- {language_note(language)}",
    ]
    if factor_levels["contracts_explicit"]:
        lines.append(f"- {return_contract_note(task_id)}")
    if factor_levels["state_guidance"]:
        lines.append("- Keep data flow locally visible with explicit intermediate state transitions.")
    lines.append("- Do not include explanations outside the single code block.")
    return "\n".join(lines) + "\n"


def build_rows() -> list[dict[str, Any]]:
    prompt_rows: list[dict[str, Any]] = []
    with (GENERATED_DIR / "prompt_records.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                prompt_rows.append(json.loads(line))

    implementations = build_implementations()
    benchmark_rows: list[dict[str, Any]] = []
    for row in prompt_rows:
        impl = implementations[row["task_id"]][row["language"]]
        benchmark_rows.append(
            {
                "study_id": row["study_id"],
                "experiment_id": f"{row['task_id']}:{row['language']}:{row['condition_id']}",
                "task_id": row["task_id"],
                "title": row["title"],
                "language": row["language"],
                "condition_id": row["condition_id"],
                "condition_label": row["condition_label"],
                "factor_levels": row["factor_levels"],
                "focus_dimensions": row["focus_dimensions"],
                "hypothesis_tags": row["hypothesis_tags"],
                "question": augment_question(row["question"], row["task_id"], row["language"], row),
                "canonical_solution": impl["canonical_solution"],
                "demo_test_func": impl["demo_test_func"],
                "full_test_func": impl["full_test_func"],
            }
        )
    return benchmark_rows


def main() -> None:
    rows = build_rows()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATA_DIR / "benchmark.jsonl", rows)
    write_csv(
        DATA_DIR / "benchmark_manifest.csv",
        [
            {
                "experiment_id": row["experiment_id"],
                "task_id": row["task_id"],
                "language": row["language"],
                "condition_id": row["condition_id"],
                "condition_label": row["condition_label"],
                "docs_rich": row["factor_levels"]["docs_rich"],
                "examples": row["factor_levels"]["examples"],
                "contracts_explicit": row["factor_levels"]["contracts_explicit"],
                "state_guidance": row["factor_levels"]["state_guidance"],
                "title": row["title"],
            }
            for row in rows
        ],
    )
    (DATA_DIR / "summary.json").write_text(
        json.dumps(
            {
                "row_count": len(rows),
                "task_count": len({row["task_id"] for row in rows}),
                "language_count": len({row["language"] for row in rows}),
                "condition_count": len({row["condition_id"] for row in rows}),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
