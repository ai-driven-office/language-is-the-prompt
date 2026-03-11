#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def row_key(row: dict[str, Any]) -> tuple[str, Any]:
    original = row.get("original_data") or {}
    absolute_line = original.get("_absolute_line_number")
    if absolute_line is not None:
        return ("line", absolute_line)

    question = (original.get("question") or row.get("question") or "").strip()
    language = (row.get("language") or original.get("language") or "").strip().lower()
    return ("question", language, question)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge targeted exec reruns into a baseline exec JSONL.")
    parser.add_argument("--base", required=True, help="Existing full exec JSONL file")
    parser.add_argument(
        "--replacement",
        action="append",
        required=True,
        help="Replacement exec JSONL file. Can be passed multiple times.",
    )
    parser.add_argument("--output", required=True, help="Path to write merged exec JSONL")
    args = parser.parse_args()

    base_path = Path(args.base)
    replacement_paths = [Path(item) for item in args.replacement]
    output_path = Path(args.output)

    base_rows = read_jsonl(base_path)
    replacements: dict[tuple[str, Any], dict[str, Any]] = {}
    for replacement_path in replacement_paths:
        for row in read_jsonl(replacement_path):
            replacements[row_key(row)] = row

    merged_rows: list[dict[str, Any]] = []
    replaced_count = 0
    for row in base_rows:
        key = row_key(row)
        replacement = replacements.get(key)
        if replacement is not None:
            merged_rows.append(replacement)
            replaced_count += 1
        else:
            merged_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, merged_rows)
    print(
        f"Merged {replaced_count} row(s) from {len(replacement_paths)} replacement file(s) into {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
