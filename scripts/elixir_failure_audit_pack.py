#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from elixir_error_taxonomy import (
    EXEC_PATH,
    first_non_pass_outcome,
    classify_failure,
    runtime_subtype,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "results" / "elixir_failure_audit"
SEED = 54


def shorten(text: str, limit: int = 240) -> str:
    collapsed = " ".join(str(text).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def load_failures() -> list[dict]:
    failures: list[dict] = []
    with EXEC_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("success"):
                continue
            stage, outcome, response = first_non_pass_outcome(row)
            original = row.get("original_data", {})
            stderr = response.get("response_extensions", {}).get("stderr", "")
            stdout = response.get("response_extensions", {}).get("stdout", "")
            category = classify_failure(outcome)
            failures.append(
                {
                    "index": row.get("index"),
                    "language": row.get("language", ""),
                    "title": original.get("question", "").splitlines()[0].strip(),
                    "question_excerpt": shorten(original.get("question", ""), 340),
                    "first_failure_stage": stage,
                    "first_failure_outcome": outcome,
                    "failure_category_auto": category,
                    "runtime_subtype_auto": runtime_subtype(outcome, response) if category == "runtime" else "",
                    "stderr_excerpt": shorten(stderr, 340),
                    "stdout_excerpt": shorten(stdout, 200),
                }
            )
    return failures


def stratified_other_sample(rows: list[dict], sample_size: int) -> list[dict]:
    rng = random.Random(SEED)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_category[row["failure_category_auto"]].append(row)
    for values in by_category.values():
        rng.shuffle(values)

    ordered_categories = ["compile", "runtime", "wrong_answer", "other"]
    picked: list[dict] = []
    while len(picked) < sample_size and any(by_category.values()):
        progressed = False
        for category in ordered_categories:
            bucket = by_category.get(category, [])
            if bucket and len(picked) < sample_size:
                picked.append(bucket.pop())
                progressed = True
        if not progressed:
            break
    return picked


def build_samples(rows: list[dict]) -> list[dict]:
    elixir_rows = [row for row in rows if row["language"] == "elixir"]
    other_rows = [row for row in rows if row["language"] != "elixir"]
    sample: list[dict] = list(elixir_rows)
    sample.extend(stratified_other_sample(other_rows, sample_size=35))
    sample = sorted(sample, key=lambda row: (row["language"], row["index"]))
    for audit_number, row in enumerate(sample, start=1):
        row["audit_id"] = f"AUD-{audit_number:03d}"
    return sample


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_readme(sample: list[dict]) -> None:
    total = len(sample)
    elixir_count = sum(1 for row in sample if row["language"] == "elixir")
    category_counts: dict[str, int] = defaultdict(int)
    for row in sample:
        category_counts[row["failure_category_auto"]] += 1
    lines = [
        "# Failure Taxonomy Audit Pack",
        "",
        "This pack is designed to strengthen the paper's failure-taxonomy section without rerunning the benchmark.",
        "",
        "## Contents",
        "",
        "- `audit_samples_blinded.csv`: reviewer-facing sheet with no automatic labels or language names.",
        "- `audit_key.csv`: key containing auto-labels and metadata for adjudication.",
        "",
        "## Recommended protocol",
        "",
        "1. Give `audit_samples_blinded.csv` to two independent reviewers.",
        "2. Ask each reviewer to fill `review_failure_category` and `review_runtime_subtype` without seeing the automatic labels.",
        "3. Compare the filled sheets to `audit_key.csv` and compute agreement after adjudication.",
        "",
        "## Sample composition",
        "",
        f"- Total rows: `{total}`",
        f"- Elixir failures included exhaustively: `{elixir_count}`",
        f"- Non-Elixir comparison failures sampled: `{total - elixir_count}`",
        f"- Category mix: compile `{category_counts['compile']}`, runtime `{category_counts['runtime']}`, wrong_answer `{category_counts['wrong_answer']}`, other `{category_counts['other']}`",
    ]
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_failures()
    sample = build_samples(rows)

    blinded_rows = []
    key_rows = []
    for row in sample:
        blinded_rows.append(
            {
                "audit_id": row["audit_id"],
                "title": row["title"],
                "question_excerpt": row["question_excerpt"],
                "first_failure_stage": row["first_failure_stage"],
                "first_failure_outcome": row["first_failure_outcome"],
                "stderr_excerpt": row["stderr_excerpt"],
                "stdout_excerpt": row["stdout_excerpt"],
                "review_failure_category": "",
                "review_runtime_subtype": "",
                "review_notes": "",
                "reviewer": "",
            }
        )
        key_rows.append(
            {
                "audit_id": row["audit_id"],
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "first_failure_stage": row["first_failure_stage"],
                "first_failure_outcome": row["first_failure_outcome"],
                "failure_category_auto": row["failure_category_auto"],
                "runtime_subtype_auto": row["runtime_subtype_auto"],
                "stderr_excerpt": row["stderr_excerpt"],
            }
        )

    write_csv(
        OUTPUT_DIR / "audit_samples_blinded.csv",
        blinded_rows,
        [
            "audit_id",
            "title",
            "question_excerpt",
            "first_failure_stage",
            "first_failure_outcome",
            "stderr_excerpt",
            "stdout_excerpt",
            "review_failure_category",
            "review_runtime_subtype",
            "review_notes",
            "reviewer",
        ],
    )
    write_csv(
        OUTPUT_DIR / "audit_key.csv",
        key_rows,
        [
            "audit_id",
            "index",
            "language",
            "title",
            "first_failure_stage",
            "first_failure_outcome",
            "failure_category_auto",
            "runtime_subtype_auto",
            "stderr_excerpt",
        ],
    )
    write_readme(sample)


if __name__ == "__main__":
    main()
