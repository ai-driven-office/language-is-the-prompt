#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_DIR = REPO_ROOT / "AutoCodeGen" / "templates" / "translate_templates"


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_template(template_name: str, template_file: str | None) -> str:
    if template_file:
        path = Path(template_file)
    else:
        path = DEFAULT_TEMPLATE_DIR / f"{template_name}.txt"
    return path.read_text(encoding="utf-8")


def build_prompt(template: str, row: dict[str, Any]) -> str:
    replacements = {
        "<<<problem>>>": row["question"],
        "<<<code>>>": row["canonical_solution"],
        "<<<demo_test>>>": row["demo_test_func"],
        "<<<full_test>>>": row["full_test_func"],
    }
    prompt = template
    for needle, value in replacements.items():
        prompt = prompt.replace(needle, value)
    return prompt


def select_rows(
    rows: list[dict[str, Any]],
    source_language: str | None,
    limit: int | None,
) -> list[tuple[int, dict[str, Any]]]:
    selected: list[tuple[int, dict[str, Any]]] = []
    for index, row in enumerate(rows, start=1):
        if source_language and row.get("language") != source_language:
            continue
        selected.append((index, row))
        if limit is not None and len(selected) >= limit:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build translation prompts for benchmark-extension languages while preserving source metadata."
    )
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--target-template", required=True, help="Template basename under AutoCodeGen/templates/translate_templates.")
    parser.add_argument("--target-language", required=True, help="Language label to store in the translated rows.")
    parser.add_argument("--source-language", help="Filter source rows by language before translation.")
    parser.add_argument("--variant", help="Optional variant/profile label to preserve in metadata.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--template-file", help="Override template path instead of target-template lookup.")
    parser.add_argument(
        "--system-prompt",
        default="",
        help="Optional system prompt for message-based generation. Defaults to empty to preserve template behavior.",
    )
    args = parser.parse_args()

    template = load_template(args.target_template, args.template_file)
    source_rows = read_jsonl(Path(args.input_file))
    selected_rows = select_rows(source_rows, args.source_language, args.limit)

    output_rows: list[dict[str, Any]] = []
    for source_index, row in selected_rows:
        prompt = build_prompt(template, row)
        output_row = {
            "messages": [
                {"role": "system", "content": args.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "language": args.target_language,
            "difficulty": row.get("difficulty"),
            "_translation_source_index": source_index,
            "_translation_source_language": row.get("language"),
            "_translation_target_template": args.target_template,
        }
        if args.variant:
            output_row["_translation_variant"] = args.variant
        output_rows.append(output_row)

    write_jsonl(Path(args.output_file), output_rows)
    print(
        f"Wrote {len(output_rows)} translation prompt rows to {args.output_file} "
        f"(template={args.target_template}, language={args.target_language})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
