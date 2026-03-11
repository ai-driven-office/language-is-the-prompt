#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROBLEM_PATTERNS = [
    re.compile(r"<translated_problem>\s*(.*?)\s*</translated_problem>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<problem>\s*(.*?)\s*</problem>", re.DOTALL | re.IGNORECASE),
]
CODE_BLOCK_PATTERN = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def extract_problem(text: str) -> str | None:
    for pattern in PROBLEM_PATTERNS:
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            if value.lower().startswith("new problem"):
                value = value[len("new problem"):].lstrip(" \n:-")
            if value:
                return value
    return None


def extract_code_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for language, body in CODE_BLOCK_PATTERN.findall(text):
        blocks.append((language.strip(), body.strip()))
    return blocks


def build_output_row(row: dict[str, Any], problem: str, blocks: list[tuple[str, str]]) -> dict[str, Any]:
    (solution_lang, solution), (demo_lang, demo_test), (full_lang, full_test) = blocks[:3]
    output_row = {
        "question": problem,
        "canonical_solution": solution,
        "demo_test_func": demo_test,
        "full_test_func": full_test,
        "language": row.get("language"),
        "difficulty": row.get("difficulty"),
        "_translation_source_index": row.get("_translation_source_index"),
        "_translation_source_language": row.get("_translation_source_language"),
        "_translation_target_template": row.get("_translation_target_template"),
        "_translation_detected_languages": [solution_lang, demo_lang, full_lang],
    }
    if row.get("_translation_variant"):
        output_row["_translation_variant"] = row["_translation_variant"]
        output_row["runtime_variant"] = row["_translation_variant"]
    return output_row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract translated benchmark rows from model outputs produced by translation prompts."
    )
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--error-file")
    parser.add_argument("--keep-output", action="store_true", help="Retain the raw model output in successful rows.")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    error_path = Path(args.error_file) if args.error_file else output_path.with_suffix(".errors.jsonl")

    if output_path.exists():
        output_path.unlink()
    if error_path.exists():
        error_path.unlink()

    rows = read_jsonl(input_path)
    success_count = 0
    error_count = 0

    for row in rows:
        output = row.get("output")
        if not isinstance(output, str) or not output.strip():
            append_jsonl(
                error_path,
                {
                    "language": row.get("language"),
                    "_translation_source_index": row.get("_translation_source_index"),
                    "error": "Missing output text",
                },
            )
            error_count += 1
            continue

        problem = extract_problem(output)
        blocks = extract_code_blocks(output)
        if not problem or len(blocks) < 3:
            append_jsonl(
                error_path,
                {
                    "language": row.get("language"),
                    "_translation_source_index": row.get("_translation_source_index"),
                    "error": "Failed to parse translated_problem tag or three code blocks",
                },
            )
            error_count += 1
            continue

        output_row = build_output_row(row, problem, blocks)
        if args.keep_output:
            output_row["output"] = output
        append_jsonl(output_path, output_row)
        success_count += 1

    print(
        f"Extracted {success_count} translated benchmark rows to {output_path}; "
        f"{error_count} rows written to {error_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
