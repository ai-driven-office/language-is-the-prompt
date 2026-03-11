#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def clean_original_row(row: dict[str, Any]) -> dict[str, Any]:
    original = dict(row.get("original_data") or {})
    original.pop("_absolute_line_number", None)
    original.pop("_relative_line_number", None)
    original.pop("extracted_code", None)
    return original


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep only exec rows whose benchmark passed and emit the original input rows.")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    input_rows = read_jsonl(Path(args.input_file))
    output_rows = [clean_original_row(row) for row in input_rows if row.get("success")]
    write_jsonl(Path(args.output_file), output_rows)
    print(f"Wrote {len(output_rows)} successful row(s) to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
