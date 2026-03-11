#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY_DIR = REPO_ROOT / "studies" / "explicit_task_panel"
GENERATED_DIR = STUDY_DIR / "generated"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def build_question(task: dict, condition: dict, language: str) -> str:
    signature = task["function_signatures"][language]
    lines = [
        f"# {task['title']}",
        "",
        "## Problem Description",
        task["summary"],
        "",
        "## Required Behavior",
    ]
    for item in task["required_behavior"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Function Contract",
            f"- Implement: `{signature}`",
        ]
    )
    if condition.get("include_contract"):
        for item in task["contract_details"]:
            lines.append(f"- {item}")
    if condition.get("include_edge_cases"):
        lines.extend(["", "## Edge Cases"])
        for item in task["edge_cases"]:
            lines.append(f"- {item}")
    if condition.get("include_examples"):
        lines.extend(["", "## Examples"])
        for example in task["examples"]:
            lines.append(
                f"- Input: `{json.dumps(example['input'], ensure_ascii=False)}` -> Output: `{json.dumps(example['expected'], ensure_ascii=False)}`"
            )
    if condition.get("extra_prompt_notes"):
        lines.extend(["", "## Additional Guidance"])
        for item in condition["extra_prompt_notes"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> None:
    study_meta = load_json(STUDY_DIR / "study.json")
    tasks = load_json(STUDY_DIR / "tasks.json")
    conditions = load_json(STUDY_DIR / "conditions.json")
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    prompt_rows: list[dict] = []
    summary = {
        "study_id": study_meta["study_id"],
        "target_languages": study_meta["target_languages"],
        "task_count": len(tasks),
        "condition_count": len(conditions),
        "row_count": 0,
    }

    for task in tasks:
        for condition in conditions:
            for language in study_meta["target_languages"]:
                prompt_rows.append(
                    {
                        "study_id": study_meta["study_id"],
                        "task_id": task["id"],
                        "title": task["title"],
                        "language": language,
                        "condition_id": condition["id"],
                        "focus_dimensions": task["focus_dimensions"],
                        "hypothesis_tags": task["hypothesis_tags"],
                        "question": build_question(task, condition, language),
                    }
                )

    summary["row_count"] = len(prompt_rows)
    (GENERATED_DIR / "panel_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (GENERATED_DIR / "prompt_records.jsonl").open("w", encoding="utf-8") as handle:
        for row in prompt_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
