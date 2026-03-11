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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def row_key(row: dict[str, Any]) -> tuple[str, Any]:
    source_index = row.get("_translation_source_index")
    if source_index is not None:
        return ("source_index", source_index)

    question = (row.get("question") or "").strip()
    language = (row.get("language") or "").strip().lower()
    return ("question", language, question)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge replacement benchmark rows into a base benchmark JSONL.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--replacement", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base_rows = read_jsonl(Path(args.base))
    replacements: dict[tuple[str, Any], dict[str, Any]] = {}
    for replacement_path in args.replacement:
        for row in read_jsonl(Path(replacement_path)):
            replacements[row_key(row)] = row

    merged_rows: list[dict[str, Any]] = []
    replaced_count = 0
    for row in base_rows:
        replacement = replacements.get(row_key(row))
        if replacement is not None:
            merged_rows.append(replacement)
            replaced_count += 1
        else:
            merged_rows.append(row)

    write_jsonl(Path(args.output), merged_rows)
    print(
        f"Merged {replaced_count} row(s) from {len(args.replacement)} replacement file(s) into {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
