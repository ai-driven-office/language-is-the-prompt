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


LANGUAGE_REPAIR_RULES = {
    "lean4": """
Critical Lean 4 repair rules:
- The final file is the solution block followed by the test block, executed with `lean --run`.
- Put imports only in the solution block. Never put imports in the test blocks.
- The test blocks may define only assertion helpers plus `def main : IO Unit := do`.
- Do not repeat the solution code, solution structures, or solution helpers in either test block.
- Prefer a conservative Lean subset: `List`, recursion, `String.splitOn`, `String.contains`, `String.startsWith`, simple helper functions.
- Avoid brittle or version-sensitive APIs such as `HashMap`, mutable arrays, `Array.get!`, `Array.set!`, `Array.mkArray`, `String.data`, `String.mk`, and `String.take`/`String.drop` when they produce `String.Slice`.
- If you need trimming, use `(String.trimAscii s).toString`.
- Test assertions must evaluate a `Bool`. Use `actual == expected` when the type derives `BEq`, or `decide (...)` when needed.
""".strip(),
    "gleam": """
Critical Gleam repair rules:
- The final file is the solution block followed by the test block, executed with `gleam run`.
- Do not use `if` anywhere. Use `case` for conditional logic.
- The test blocks may define only assertion helpers plus `pub fn main()`.
- Do not repeat the solution code in the test blocks.
- If you use `Option`, `Result`, `Some`, or `None`, import them explicitly.
- Prefer simple standard-library code only.
""".strip(),
}


def summarize_exec_error(exec_row: dict[str, Any]) -> str:
    chunks: list[str] = []
    for phase_key in ("demo_test_result", "full_test_result"):
        phase = exec_row.get(phase_key) or {}
        response = (phase.get("response") or {}).get("response_extensions") or {}
        stdout = (response.get("stdout") or "").strip()
        stderr = (response.get("stderr") or "").strip()
        if not stdout and not stderr:
            continue
        chunks.append(f"[{phase_key}]")
        if stdout:
            chunks.append(stdout)
        if stderr:
            chunks.append(stderr)
    return "\n\n".join(chunks).strip()


def build_prompt(language: str, original: dict[str, Any], error_text: str) -> str:
    language_name = {"lean4": "Lean 4", "gleam": "Gleam 1.x"}.get(language, language)
    rules = LANGUAGE_REPAIR_RULES.get(language, "").strip()
    return f"""You are repairing a translated AutoCodeBenchmark row for {language_name}.

The current translated benchmark does not compile or run correctly. Fix it so that:
1. The problem statement still clearly asks for an implementation in {language_name}.
2. The translated reference solution is valid, runnable {language_name}.
3. The demo and full test blocks are valid and runnable after appending them below the solution block in the same file.
4. The solution and tests preserve the original benchmark intent as closely as possible.
5. The solution block and test blocks remain separate.

{rules}

Return exactly this shape:
<translated_problem>
...
</translated_problem>

<translated_reference_solution>
```{language}
...
```
</translated_reference_solution>

<demo_test_cases>
```{language}
...
```
</demo_test_cases>

<full_test_cases>
```{language}
...
```
</full_test_cases>

Current translated problem:
<translated_problem>
{original.get("question", "").strip()}
</translated_problem>

Current translated reference solution:
```{language}
{original.get("canonical_solution", "").strip()}
```

Current demo test block:
```{language}
{original.get("demo_test_func", "").strip()}
```

Current full test block:
```{language}
{original.get("full_test_func", "").strip()}
```

Compiler/runtime errors from the failed execution:
{error_text or "(no error text captured)"}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build repair prompts for translated benchmark rows that failed canonical execution."
    )
    parser.add_argument("--input-file", required=True, help="Canonical exec JSONL with original_data attached.")
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--system-prompt", default="")
    args = parser.parse_args()

    input_rows = read_jsonl(Path(args.input_file))
    output_rows: list[dict[str, Any]] = []
    for row in input_rows:
        if row.get("success"):
            continue
        original = row.get("original_data") or {}
        prompt = build_prompt(args.language, original, summarize_exec_error(row))
        output_row = {
            "messages": [
                {"role": "system", "content": args.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "language": args.language,
            "difficulty": original.get("difficulty"),
            "_translation_source_index": original.get("_translation_source_index"),
            "_translation_source_language": original.get("_translation_source_language"),
            "_translation_target_template": original.get("_translation_target_template"),
            "_repair_source": "canonical_exec",
        }
        if original.get("runtime_variant"):
            output_row["runtime_variant"] = original["runtime_variant"]
        if original.get("_translation_variant"):
            output_row["_translation_variant"] = original["_translation_variant"]
        output_rows.append(output_row)

    write_jsonl(Path(args.output_file), output_rows)
    print(f"Wrote {len(output_rows)} repair prompt row(s) to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
