#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = REPO_ROOT / "results"
MANIFEST_PATH = REPO_ROOT / "reports" / "elixir_hypothesis_suites.yaml"
DEFAULT_EXEC_PATH = REPO_ROOT / "outputs" / "openai-5-4-medium-adaptive.native-fixed.exec.jsonl"
SUITE_ORDER = [
    "suite_a",
    "suite_b",
    "suite_c",
    "suite_d",
    "suite_e",
    "suite_f",
    "suite_g",
    "suite_h",
    "suite_i",
]

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_!?]*")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass
class Row:
    index: int
    language: str
    success: bool
    difficulty: str
    question: str
    canonical: str
    demo_test: str
    full_test: str
    full_outcome: str
    title: str


def load_manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            original = payload.get("original_data") or {}
            full_response = ((payload.get("full_test_result") or {}).get("response") or {})
            question = original.get("question") or ""
            rows.append(
                Row(
                    index=int(payload.get("index")),
                    language=payload.get("language") or "unknown",
                    success=bool(payload.get("success")),
                    difficulty=original.get("difficulty") or "unknown",
                    question=question,
                    canonical=original.get("canonical_solution") or "",
                    demo_test=original.get("demo_test_func") or "",
                    full_test=original.get("full_test_func") or "",
                    full_outcome=full_response.get("exec_outcome") or "MISSING",
                    title=extract_title(question),
                )
            )
    return rows


def extract_title(question: str) -> str:
    for line in question.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return question.splitlines()[0].strip() if question.strip() else "Untitled"


def safe_rate(passed: int, total: int) -> float:
    return passed / total if total else 0.0


def pct(value: float) -> float:
    return round(value * 100.0, 1)


def median_int(values: list[float]) -> int:
    if not values:
        return 0
    return int(round(statistics.median(values)))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = mean(xs)
    mean_y = mean(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    if not denom:
        return 0.0
    return sum(a * b for a, b in zip(dx, dy)) / denom


def tokenize(text: str) -> set[str]:
    return {match.group(0).lower() for match in TOKEN_RE.finditer(text)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def shannon_from_counter(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in counter.values():
        p = value / total
        entropy -= p * math.log2(p)
    return entropy


def line_count(text: str) -> int:
    return len(text.splitlines()) if text else 0


def count_markers(text: str, markers: list[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(marker) for marker in markers)


def count_code_blocks(text: str) -> int:
    return text.count("```") // 2


def count_bullets(text: str) -> int:
    total = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* ") or re.match(r"^\d+\.\s", stripped):
            total += 1
    return total


def section_presence(text: str, names: list[str]) -> int:
    lowered = text.lower()
    return int(any(name in lowered for name in names))


def leading_indent_stats(text: str) -> tuple[float, float]:
    indents = [len(line) - len(line.lstrip(" ")) for line in text.splitlines() if line.strip()]
    if not indents:
        return 0.0, 0.0
    counter = Counter(indents)
    return shannon_from_counter(counter), stdev(indents)


def line_length_entropy(text: str) -> float:
    lengths = [min(len(line.rstrip()), 160) // 10 for line in text.splitlines() if line.strip()]
    return shannon_from_counter(Counter(lengths))


def identifier_style_mix(text: str) -> int:
    styles: set[str] = set()
    for token in IDENT_RE.findall(text):
        if token.startswith("__"):
            styles.add("dunder")
        elif "-" in token:
            styles.add("kebab")
        elif "_" in token:
            styles.add("snake")
        elif token[:1].isupper():
            styles.add("pascal")
        elif re.search(r"[a-z][A-Z]", token):
            styles.add("camel")
        else:
            styles.add("plain")
    return len(styles)


def comment_line_count(language: str, text: str) -> int:
    prefixes = {
        "python": "#",
        "shell": "#",
        "ruby": "#",
        "perl": "#",
        "r": "#",
        "racket": ";",
        "julia": "#",
        "elixir": "#",
        "go": "//",
        "java": "//",
        "javascript": "//",
        "typescript": "//",
        "typescript_effect": "//",
        "swift": "//",
        "dart": "//",
        "scala": "//",
        "kotlin": "//",
        "cpp": "//",
        "csharp": "//",
        "php": "//",
        "rust": "//",
        "gleam": "//",
        "lean4": "--",
    }
    prefix = prefixes.get(language, "//")
    return sum(1 for line in text.splitlines() if line.strip().startswith(prefix))


def docs_features(row: Row) -> dict:
    question = row.question
    example_markers = count_markers(question, ["example", "usage", "doctest"])
    constraints = section_presence(question, ["constraint", "requirements"])
    notes = section_presence(question, ["note", "testing", "edge case"])
    headings = sum(1 for line in question.splitlines() if line.strip().startswith("#"))
    code_blocks = count_code_blocks(question)
    bullets = count_bullets(question)
    score = (
        min(headings, 6) * 1.5
        + min(code_blocks, 4) * 3.0
        + min(bullets, 12) * 0.4
        + min(example_markers, 5) * 2.0
        + constraints * 2.0
        + notes * 1.5
        + min(len(question) / 600.0, 6.0)
    )
    return {
        "question_chars": len(question),
        "question_lines": line_count(question),
        "headings": headings,
        "code_blocks": code_blocks,
        "bullets": bullets,
        "example_markers": example_markers,
        "has_constraints": constraints,
        "has_notes": notes,
        "docs_score": round(score, 2),
    }


def cleanliness_features(row: Row) -> dict:
    text = row.canonical
    lines = text.splitlines()
    nonblank = [line for line in lines if line.strip()]
    blank_ratio = safe_rate(len(lines) - len(nonblank), len(lines))
    comment_ratio = safe_rate(comment_line_count(row.language, text), max(len(nonblank), 1))
    long_line_ratio = safe_rate(sum(1 for line in nonblank if len(line) > 100), max(len(nonblank), 1))
    avg_line_len = mean([len(line.rstrip()) for line in nonblank])
    indent_entropy, indent_stdev = leading_indent_stats(text)
    style_mix = identifier_style_mix(text)
    score = (
        100.0
        - min(long_line_ratio * 120.0, 30.0)
        - min(indent_entropy * 8.0, 20.0)
        - min(abs(blank_ratio - 0.12) * 80.0, 10.0)
        - min(max(style_mix - 3, 0) * 2.0, 12.0)
        + min(comment_ratio * 20.0, 8.0)
    )
    return {
        "canonical_chars": len(text),
        "canonical_lines": len(lines),
        "blank_ratio": round(blank_ratio, 4),
        "comment_ratio": round(comment_ratio, 4),
        "long_line_ratio": round(long_line_ratio, 4),
        "avg_line_length": round(avg_line_len, 2),
        "indent_entropy": round(indent_entropy, 3),
        "indent_stdev": round(indent_stdev, 2),
        "identifier_style_mix": style_mix,
        "cleanliness_score": round(max(score, 0.0), 2),
    }


def style_features(row: Row) -> dict:
    text = row.canonical
    indent_entropy, indent_stdev = leading_indent_stats(text)
    length_entropy = line_length_entropy(text)
    style_mix = identifier_style_mix(text)
    punctuation_counter = Counter(char for char in text if char in "{}[]()<>:=|,.")
    punctuation_entropy = shannon_from_counter(punctuation_counter)
    score = indent_entropy + length_entropy + punctuation_entropy + max(style_mix - 1, 0) * 0.25
    stability = max(0.0, 100.0 - score * 12.0 - min(indent_stdev * 4.0, 18.0))
    return {
        "style_entropy": round(score, 3),
        "style_stability_score": round(stability, 2),
        "indent_entropy": round(indent_entropy, 3),
        "line_length_entropy": round(length_entropy, 3),
        "punctuation_entropy": round(punctuation_entropy, 3),
        "identifier_style_mix": style_mix,
    }


def control_flow_features(row: Row) -> dict:
    text = row.canonical
    lowered = text.lower()
    pattern_count = (
        lowered.count("{:ok")
        + lowered.count("{:error")
        + lowered.count("%{")
        + lowered.count("[head |")
        + len(re.findall(r"^\s*def[p]?\s+\w+\([^)]*\)\s+when\b", text, flags=re.M))
        + len(re.findall(r"^\s*def[p]?\s+\w+\([^)]*\)\s+do\b", text, flags=re.M))
    )
    dispatch_count = count_markers(lowered, ["case ", "with ", "cond ", "match ", "switch "])
    imperative_count = count_markers(lowered, ["if ", "else", "elseif", "elif ", "while ", "for "])
    score = pattern_count * 1.8 + dispatch_count * 1.4 - imperative_count * 0.4
    return {
        "pattern_signal_count": pattern_count,
        "dispatch_count": dispatch_count,
        "imperative_branch_count": imperative_count,
        "control_flow_score": round(score, 2),
    }


def result_contract_features(row: Row) -> dict:
    text = row.canonical.lower()
    tagged_tuple_count = text.count("{:ok") + text.count("{:error")
    typed_result_count = count_markers(text, ["result<", "either", "option", "ok(", "err(", "some(", "none"])
    map_contract_count = count_markers(text, ["map<", "dict", "map[", "%{"])
    boolean_contract_count = count_markers(text, ["true", "false"])
    contract_score = tagged_tuple_count * 2.0 + typed_result_count * 1.6 + map_contract_count * 0.6 - boolean_contract_count * 0.15
    return {
        "tagged_tuple_count": tagged_tuple_count,
        "typed_result_count": typed_result_count,
        "map_contract_count": map_contract_count,
        "boolean_contract_count": boolean_contract_count,
        "contract_score": round(contract_score, 2),
    }


def mutability_features(row: Row) -> dict:
    text = row.canonical.lower()
    assignment_count = len(re.findall(r"(?<![=!<>])=(?!=)", row.canonical))
    update_ops = count_markers(
        text,
        ["append", "push", "pop", "insert", "remove", "delete", "splice", "sort!", "update", "set_", "put_", "put!", "<<"],
    )
    state_words = count_markers(row.question.lower(), ["state", "cache", "counter", "session", "balance", "queue", "stack", "update"])
    burden = assignment_count * 0.7 + update_ops * 1.3 + state_words * 0.9
    immutability_bonus = 2.0 if row.language == "elixir" else 0.0
    return {
        "assignment_count": assignment_count,
        "update_operation_count": update_ops,
        "state_word_count": state_words,
        "mutability_burden_score": round(max(burden - immutability_bonus, 0.0), 2),
    }


def alignment_features(row: Row) -> dict:
    q_tokens = tokenize(row.question)
    c_tokens = tokenize(row.canonical)
    d_tokens = tokenize(row.demo_test)
    f_tokens = tokenize(row.full_test)
    q_c = jaccard(q_tokens, c_tokens)
    q_t = jaccard(q_tokens, d_tokens | f_tokens)
    c_t = jaccard(c_tokens, d_tokens | f_tokens)
    overlap_score = (q_c * 0.4) + (q_t * 0.3) + (c_t * 0.3)
    return {
        "question_canonical_overlap": round(q_c, 4),
        "question_test_overlap": round(q_t, 4),
        "canonical_test_overlap": round(c_t, 4),
        "alignment_score": round(overlap_score * 100.0, 2),
    }


def build_feature_rows(rows: list[Row]) -> list[dict]:
    records: list[dict] = []
    for row in rows:
        record = {
            "index": row.index,
            "language": row.language,
            "difficulty": row.difficulty,
            "success": int(row.success),
            "full_outcome": row.full_outcome,
            "title": row.title,
        }
        record.update(docs_features(row))
        record.update(cleanliness_features(row))
        record.update(style_features(row))
        record.update(control_flow_features(row))
        record.update(result_contract_features(row))
        record.update(mutability_features(row))
        record.update(alignment_features(row))
        records.append(record)
    return records


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fieldnames:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def suite_dir(short_id: str) -> Path:
    return RESULTS_ROOT / f"elixir_{short_id}"


def summarize_by_language(records: list[dict], feature_names: list[str], sort_key: str = "pass_rate") -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record["language"]].append(record)
    summary: list[dict] = []
    for language, rows in sorted(grouped.items()):
        values = {name: [float(row[name]) for row in rows] for name in feature_names}
        success_values = [float(row["success"]) for row in rows]
        row_summary = {
            "language": language,
            "rows": len(rows),
            "passed": sum(int(row["success"]) for row in rows),
            "pass_rate": pct(safe_rate(sum(int(row["success"]) for row in rows), len(rows))),
        }
        for name in feature_names:
            row_summary[f"mean_{name}"] = round(mean(values[name]), 3)
        if feature_names:
            row_summary["success_feature_corr"] = round(
                pearson([float(row[feature_names[0]]) for row in rows], success_values), 3
            )
        summary.append(row_summary)
    return sorted(summary, key=lambda row: row[sort_key], reverse=True)


def write_suite_status(out_dir: Path, suite_id: str, title: str, status: str, generated_files: list[str], notes: list[str]) -> None:
    payload = {
        "suite_id": suite_id,
        "title": title,
        "status": status,
        "generated_files": generated_files,
        "notes": notes,
    }
    write_json(out_dir / "status.json", payload)


def write_suite_readme(out_dir: Path, suite_id: str, title: str, theory: str, null_hypothesis: str, notes: list[str]) -> None:
    lines = [
        f"# {suite_id}: {title}",
        "",
        "## Theory",
        "",
        theory,
        "",
        "## Null hypothesis",
        "",
        null_hypothesis,
        "",
        "## Current implementation state",
        "",
    ]
    for note in notes:
        lines.append(f"- {note}")
    lines.append("")
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def manifest_entry(manifest: dict, suite_key: str) -> dict:
    for entry in manifest.get("suites", []):
        if entry["id"].startswith(f"{suite_key}_"):
            return entry
    raise KeyError(suite_key)


def render_top_table(rows: list[dict], columns: list[tuple[str, str]], limit: int = 8) -> list[str]:
    lines = ["| " + " | ".join(label for _, label in columns) + " |", "|" + "|".join("---:" if i else "---" for i, _ in enumerate(columns)) + "|"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(str(row[key]) for key, _ in columns) + " |")
    return lines


def run_suite_a(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_a")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["docs_score", "question_chars", "code_blocks", "example_markers"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "docs_score": row["docs_score"],
            "question_chars": row["question_chars"],
            "headings": row["headings"],
            "code_blocks": row["code_blocks"],
            "example_markers": row["example_markers"],
            "has_constraints": row["has_constraints"],
            "has_notes": row["has_notes"],
            "title": row["title"],
        }
        for row in records
    ]
    experiment_matrix = []
    for row in sorted(task_rows, key=lambda item: (item["language"], -item["docs_score"]))[:120]:
        experiment_matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "condition_1": "no_docs",
                "condition_2": "signature_only",
                "condition_3": "reference_no_examples",
                "condition_4": "reference_with_examples",
            }
        )
    write_csv(out_dir / "suite_a_docs_quality.csv", summary)
    write_csv(out_dir / "suite_a_docs_quality_task_level.csv", task_rows)
    write_csv(out_dir / "suite_a_docs_experiment_matrix.csv", experiment_matrix)
    lines = [
        "# Suite A: Documentation Quality",
        "",
        "This baseline uses benchmark prompt structure as a documentation proxy. It is not the final causal experiment, but it gives a reproducible starting point before active doc-ablation runs.",
        "",
        "## Top languages by pass rate",
        "",
    ]
    lines.extend(
        render_top_table(
            summary,
            [
                ("language", "Language"),
                ("pass_rate", "Pass Rate"),
                ("mean_docs_score", "Mean Docs Score"),
                ("mean_code_blocks", "Mean Code Blocks"),
                ("mean_example_markers", "Mean Example Markers"),
                ("success_feature_corr", "Docs/Success Corr"),
            ],
        )
    )
    (out_dir / "suite_a_docs_quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_a")
    notes = [
        "Baseline metrics computed from current benchmark prompts.",
        "Experiment matrix generated for doc-ablation reruns.",
    ]
    write_suite_readme(out_dir, "suite_a", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_a_docs_quality.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_a_docs_quality_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_a_docs_experiment_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_a_docs_quality.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_a", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_b(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_b")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["cleanliness_score", "comment_ratio", "long_line_ratio", "avg_line_length"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "cleanliness_score": row["cleanliness_score"],
            "comment_ratio": row["comment_ratio"],
            "long_line_ratio": row["long_line_ratio"],
            "avg_line_length": row["avg_line_length"],
            "indent_entropy": row["indent_entropy"],
            "identifier_style_mix": row["identifier_style_mix"],
            "title": row["title"],
        }
        for row in records
    ]
    repo_matrix = [
        {"language": "elixir", "ecosystem": "phoenix", "repo_focus": "docs + typespec + tests", "condition": "clean_vs_degraded"},
        {"language": "python", "ecosystem": "fastapi", "repo_focus": "docs + tests + type hints", "condition": "clean_vs_degraded"},
        {"language": "typescript", "ecosystem": "effect", "repo_focus": "schema-rich service modules", "condition": "clean_vs_degraded"},
        {"language": "ruby", "ecosystem": "rails", "repo_focus": "docs + examples + callbacks", "condition": "clean_vs_degraded"},
    ]
    write_csv(out_dir / "suite_b_corpus_quality.csv", summary)
    write_csv(out_dir / "suite_b_corpus_quality_task_level.csv", task_rows)
    write_csv(out_dir / "suite_b_corpus_study_matrix.csv", repo_matrix)
    lines = [
        "# Suite B: Corpus Quality and Cleanliness",
        "",
        "This baseline treats canonical solutions as a local proxy for public-corpus cleanliness. The actual causal version still needs matched real repos, but the scorecard is now runnable.",
        "",
        "## Top languages by cleanliness proxy",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_cleanliness_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_cleanliness_score", "Mean Cleanliness"),
                ("pass_rate", "Pass Rate"),
                ("mean_comment_ratio", "Comment Ratio"),
                ("mean_long_line_ratio", "Long-Line Ratio"),
                ("success_feature_corr", "Cleanliness/Success Corr"),
            ],
        )
    )
    (out_dir / "suite_b_corpus_quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_b")
    notes = [
        "Local cleanliness proxy computed from canonical solutions.",
        "Real-corpus repo matrix emitted for future clean-vs-degraded benchmark runs.",
    ]
    write_suite_readme(out_dir, "suite_b", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_b_corpus_quality.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_b_corpus_quality_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_b_corpus_study_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_b_corpus_quality.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_b", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_c(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_c")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["style_stability_score", "style_entropy", "indent_entropy", "line_length_entropy"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "style_stability_score": row["style_stability_score"],
            "style_entropy": row["style_entropy"],
            "indent_entropy": row["indent_entropy"],
            "line_length_entropy": row["line_length_entropy"],
            "punctuation_entropy": row["punctuation_entropy"],
            "identifier_style_mix": row["identifier_style_mix"],
            "title": row["title"],
        }
        for row in records
    ]
    experiment_matrix = []
    for row in sorted(task_rows, key=lambda item: (item["language"], item["style_stability_score"]), reverse=True)[:120]:
        experiment_matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "condition_1": "formatter_normalized",
                "condition_2": "style_divergent",
                "condition_3": "deliberately_noisy",
            }
        )
    write_csv(out_dir / "suite_c_stylistic_entropy.csv", summary)
    write_csv(out_dir / "suite_c_stylistic_entropy_task_level.csv", task_rows)
    write_csv(out_dir / "suite_c_stylistic_entropy_matrix.csv", experiment_matrix)
    lines = [
        "# Suite C: Stylistic Entropy and Formatter Strength",
        "",
        "This baseline measures stylistic stability in canonical solutions and generates perturbation conditions for active reruns.",
        "",
        "## Most stable languages by local proxy",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_style_stability_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_style_stability_score", "Stability Score"),
                ("pass_rate", "Pass Rate"),
                ("mean_style_entropy", "Style Entropy"),
                ("mean_indent_entropy", "Indent Entropy"),
                ("success_feature_corr", "Stability/Success Corr"),
            ],
        )
    )
    (out_dir / "suite_c_stylistic_entropy.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_c")
    notes = [
        "Style and formatting proxies computed from current canonical solutions.",
        "Perturbation matrix generated for normalized-vs-noisy reruns.",
    ]
    write_suite_readme(out_dir, "suite_c", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_c_stylistic_entropy.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_c_stylistic_entropy_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_c_stylistic_entropy_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_c_stylistic_entropy.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_c", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_d(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_d")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["control_flow_score", "pattern_signal_count", "dispatch_count", "imperative_branch_count"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "control_flow_score": row["control_flow_score"],
            "pattern_signal_count": row["pattern_signal_count"],
            "dispatch_count": row["dispatch_count"],
            "imperative_branch_count": row["imperative_branch_count"],
            "title": row["title"],
        }
        for row in records
    ]
    matrix = []
    selected = sorted(task_rows, key=lambda item: (item["language"] == "elixir", item["control_flow_score"]), reverse=True)[:120]
    for row in selected:
        matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "variant_1": "function_head_or_pattern_matching",
                "variant_2": "case_or_with_dispatch",
                "variant_3": "imperative_branching",
            }
        )
    write_csv(out_dir / "suite_d_control_flow.csv", summary)
    write_csv(out_dir / "suite_d_control_flow_task_level.csv", task_rows)
    write_csv(out_dir / "suite_d_control_flow_matrix.csv", matrix)
    lines = [
        "# Suite D: Pattern Matching and Explicit Control Flow",
        "",
        "This baseline scores how explicit each language's canonical solutions are about dispatch and branching, then emits a paired-variant task matrix for the real ablation benchmark.",
        "",
        "## Languages with strongest explicit-control-flow proxy",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_control_flow_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_control_flow_score", "Control-Flow Score"),
                ("pass_rate", "Pass Rate"),
                ("mean_pattern_signal_count", "Pattern Signals"),
                ("mean_dispatch_count", "Dispatch Count"),
                ("mean_imperative_branch_count", "Imperative Branches"),
            ],
        )
    )
    (out_dir / "suite_d_control_flow.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_d")
    notes = [
        "Control-flow legibility proxy computed from canonical solutions.",
        "Paired control-flow intervention matrix generated for future reruns.",
    ]
    write_suite_readme(out_dir, "suite_d", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_d_control_flow.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_d_control_flow_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_d_control_flow_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_d_control_flow.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_d", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_e(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_e")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["contract_score", "tagged_tuple_count", "typed_result_count", "boolean_contract_count"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "contract_score": row["contract_score"],
            "tagged_tuple_count": row["tagged_tuple_count"],
            "typed_result_count": row["typed_result_count"],
            "map_contract_count": row["map_contract_count"],
            "boolean_contract_count": row["boolean_contract_count"],
            "title": row["title"],
        }
        for row in records
    ]
    matrix = []
    for row in sorted(task_rows, key=lambda item: (item["language"] == "elixir", item["contract_score"]), reverse=True)[:120]:
        matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "variant_1": "explicit_tagged_result_contract",
                "variant_2": "typed_result_wrapper",
                "variant_3": "implicit_boolean_or_nil_contract",
            }
        )
    write_csv(out_dir / "suite_e_result_contracts.csv", summary)
    write_csv(out_dir / "suite_e_result_contracts_task_level.csv", task_rows)
    write_csv(out_dir / "suite_e_result_contracts_matrix.csv", matrix)
    lines = [
        "# Suite E: Result Contracts and Tagged Tuples",
        "",
        "This baseline scores explicitness of return-shape contracts and prepares a contract-style ablation set.",
        "",
        "## Languages with strongest explicit-result proxy",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_contract_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_contract_score", "Contract Score"),
                ("pass_rate", "Pass Rate"),
                ("mean_tagged_tuple_count", "Tagged Tuples"),
                ("mean_typed_result_count", "Typed Results"),
                ("mean_boolean_contract_count", "Boolean Contracts"),
            ],
        )
    )
    (out_dir / "suite_e_result_contracts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_e")
    notes = [
        "Return-contract proxy computed from canonical solutions.",
        "Contract-ablation intervention matrix generated for future reruns.",
    ]
    write_suite_readme(out_dir, "suite_e", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_e_result_contracts.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_e_result_contracts_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_e_result_contracts_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_e_result_contracts.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_e", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_f(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_f")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["mutability_burden_score", "assignment_count", "update_operation_count", "state_word_count"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "mutability_burden_score": row["mutability_burden_score"],
            "assignment_count": row["assignment_count"],
            "update_operation_count": row["update_operation_count"],
            "state_word_count": row["state_word_count"],
            "title": row["title"],
        }
        for row in records
    ]
    matrix = []
    for row in sorted(task_rows, key=lambda item: item["mutability_burden_score"], reverse=True)[:120]:
        matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "condition_1": "immutable_reference_solution",
                "condition_2": "controlled_mutable_solution",
                "condition_3": "stateful_incremental_solution",
            }
        )
    write_csv(out_dir / "suite_f_mutability.csv", summary)
    write_csv(out_dir / "suite_f_mutability_task_level.csv", task_rows)
    write_csv(out_dir / "suite_f_mutability_matrix.csv", matrix)
    lines = [
        "# Suite F: Hidden State and Mutability Burden",
        "",
        "This baseline estimates mutability burden from canonical solutions and benchmark prompts, then emits a state-vs-immutability intervention matrix.",
        "",
        "## Highest mutability burden by language",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_mutability_burden_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_mutability_burden_score", "Mutability Burden"),
                ("pass_rate", "Pass Rate"),
                ("mean_assignment_count", "Assignments"),
                ("mean_update_operation_count", "Update Ops"),
                ("mean_state_word_count", "State Words"),
            ],
        )
    )
    (out_dir / "suite_f_mutability.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_f")
    notes = [
        "Mutability-burden proxy computed from current artifacts.",
        "Immutable-vs-stateful intervention matrix generated for future reruns.",
    ]
    write_suite_readme(out_dir, "suite_f", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_f_mutability.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_f_mutability_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_f_mutability_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_f_mutability.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_f", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_g(manifest: dict, records: list[dict]) -> list[str]:
    out_dir = suite_dir("suite_g")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_by_language(
        records,
        ["alignment_score", "question_canonical_overlap", "question_test_overlap", "canonical_test_overlap"],
    )
    task_rows = [
        {
            "index": row["index"],
            "language": row["language"],
            "difficulty": row["difficulty"],
            "success": row["success"],
            "alignment_score": row["alignment_score"],
            "question_canonical_overlap": row["question_canonical_overlap"],
            "question_test_overlap": row["question_test_overlap"],
            "canonical_test_overlap": row["canonical_test_overlap"],
            "title": row["title"],
        }
        for row in records
    ]
    matrix = []
    for row in sorted(task_rows, key=lambda item: item["alignment_score"], reverse=True)[:120]:
        matrix.append(
            {
                "index": row["index"],
                "language": row["language"],
                "title": row["title"],
                "difficulty": row["difficulty"],
                "condition_1": "aligned_docs_examples_tests",
                "condition_2": "docs_without_examples",
                "condition_3": "misaligned_examples_or_tests",
            }
        )
    write_csv(out_dir / "suite_g_alignment.csv", summary)
    write_csv(out_dir / "suite_g_alignment_task_level.csv", task_rows)
    write_csv(out_dir / "suite_g_alignment_matrix.csv", matrix)
    lines = [
        "# Suite G: Documentation, Test, and Code Alignment",
        "",
        "This baseline measures lexical alignment across prompt, canonical solution, and tests, then emits an alignment-vs-misalignment rerun matrix.",
        "",
        "## Highest local alignment by language",
        "",
    ]
    lines.extend(
        render_top_table(
            sorted(summary, key=lambda row: row["mean_alignment_score"], reverse=True),
            [
                ("language", "Language"),
                ("mean_alignment_score", "Alignment Score"),
                ("pass_rate", "Pass Rate"),
                ("mean_question_canonical_overlap", "Q/Code Overlap"),
                ("mean_question_test_overlap", "Q/Test Overlap"),
                ("mean_canonical_test_overlap", "Code/Test Overlap"),
            ],
        )
    )
    (out_dir / "suite_g_alignment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_g")
    notes = [
        "Local alignment proxy computed from prompts, canonical solutions, and tests.",
        "Alignment-ablation matrix generated for future reruns.",
    ]
    write_suite_readme(out_dir, "suite_g", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_g_alignment.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_g_alignment_task_level.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_g_alignment_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_g_alignment.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_g", entry["title"], "implemented_baseline", generated, notes)
    return generated


def run_suite_h() -> list[str]:
    subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "elixir_suite_h_artifact_controls.py")], check=True)
    return [
        "results/elixir_suite_h/suite_h_artifact_controls.csv",
        "results/elixir_suite_h/suite_h_artifact_controls_by_difficulty.csv",
        "results/elixir_suite_h/suite_h_artifact_controls.json",
        "results/elixir_suite_h/suite_h_artifact_controls.md",
    ]


def run_suite_i(manifest: dict) -> list[str]:
    out_dir = suite_dir("suite_i")
    out_dir.mkdir(parents=True, exist_ok=True)
    task_matrix = [
        {
            "language": "elixir",
            "framework": "phoenix_live_view",
            "repo_task": "Add authenticated settings flow with LiveView validation and regression tests",
            "acceptance": "unit + integration tests green",
            "priority": "highest",
            "status": "ready_for_repo_selection",
        },
        {
            "language": "elixir",
            "framework": "ecto",
            "repo_task": "Add transactional import pipeline with clear error tuples and tests",
            "acceptance": "property + integration tests green",
            "priority": "highest",
            "status": "ready_for_repo_selection",
        },
        {
            "language": "elixir",
            "framework": "genserver",
            "repo_task": "Implement supervised GenServer retry coordination with telemetry assertions",
            "acceptance": "process + supervision tests green",
            "priority": "high",
            "status": "ready_for_repo_selection",
        },
        {
            "language": "python",
            "framework": "django",
            "repo_task": "Add authenticated settings form analogue with model/form validation and tests",
            "acceptance": "unit + integration tests green",
            "priority": "highest",
            "status": "ready_for_repo_selection",
        },
        {
            "language": "javascript",
            "framework": "express",
            "repo_task": "Add authenticated settings workflow with request validation and integration tests",
            "acceptance": "unit + integration tests green",
            "priority": "highest",
            "status": "ready_for_repo_selection",
        },
        {
            "language": "ruby",
            "framework": "rails",
            "repo_task": "Add transactional import pipeline with callback-heavy validations and tests",
            "acceptance": "unit + integration tests green",
            "priority": "high",
            "status": "ready_for_repo_selection",
        },
    ]
    scorecard = [
        {"metric": "task_completion_rate", "definition": "Share of repo tasks completed without manual repair"},
        {"metric": "edit_correctness", "definition": "Review judgment on changed files"},
        {"metric": "test_pass_rate", "definition": "Share of tasks finishing green"},
        {"metric": "regression_rate", "definition": "Share of tasks introducing failing unrelated tests"},
        {"metric": "time_to_fix", "definition": "Wall-clock to first passing fix"},
    ]
    write_csv(out_dir / "suite_i_repo_scale_task_matrix.csv", task_matrix)
    write_csv(out_dir / "suite_i_repo_scale_scorecard.csv", scorecard)
    lines = [
        "# Suite I: Repo-Scale Realism",
        "",
        "Repo-scale realism cannot be claimed from the snippet benchmark alone. This suite package defines the first cross-language repo tasks and the scorecard that will be used once target repos are locked.",
        "",
        "## Planned task matrix",
        "",
    ]
    lines.extend(
        render_top_table(
            task_matrix,
            [
                ("language", "Language"),
                ("framework", "Framework"),
                ("repo_task", "Repo Task"),
                ("acceptance", "Acceptance"),
                ("priority", "Priority"),
                ("status", "Status"),
            ],
            limit=len(task_matrix),
        )
    )
    (out_dir / "suite_i_repo_scale.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    entry = manifest_entry(manifest, "suite_i")
    notes = [
        "Repo-scale suite scaffolded with concrete task matrix and scorecard.",
        "Waiting on repo selection and active model runs.",
    ]
    write_suite_readme(out_dir, "suite_i", entry["title"], entry["theory"], entry["null_hypothesis"], notes)
    generated = [
        str((out_dir / "suite_i_repo_scale_task_matrix.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_i_repo_scale_scorecard.csv").relative_to(REPO_ROOT)),
        str((out_dir / "suite_i_repo_scale.md").relative_to(REPO_ROOT)),
    ]
    write_suite_status(out_dir, "suite_i", entry["title"], "implemented_scaffold", generated, notes)
    return generated


def run_all(selected: str, exec_path: Path) -> dict[str, list[str]]:
    manifest = load_manifest()
    results: dict[str, list[str]] = {}
    if selected == "suite_h":
        results["suite_h"] = run_suite_h()
        return results
    if selected == "suite_i":
        results["suite_i"] = run_suite_i(manifest)
        return results

    rows = load_rows(exec_path)
    records = build_feature_rows(rows)
    runners = {
        "suite_a": lambda: run_suite_a(manifest, records),
        "suite_b": lambda: run_suite_b(manifest, records),
        "suite_c": lambda: run_suite_c(manifest, records),
        "suite_d": lambda: run_suite_d(manifest, records),
        "suite_e": lambda: run_suite_e(manifest, records),
        "suite_f": lambda: run_suite_f(manifest, records),
        "suite_g": lambda: run_suite_g(manifest, records),
        "suite_h": run_suite_h,
        "suite_i": lambda: run_suite_i(manifest),
    }
    if selected == "all":
        for suite_id in SUITE_ORDER:
            results[suite_id] = runners[suite_id]()
    else:
        results[selected] = runners[selected]()
    write_json(RESULTS_ROOT / "elixir_suite_index.json", results)
    return results


def parse_args() -> tuple[str, Path]:
    suite = sys.argv[1] if len(sys.argv) > 1 else "all"
    exec_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_EXEC_PATH
    if suite not in {"all", *SUITE_ORDER}:
        raise SystemExit(f"unknown suite: {suite}")
    return suite, exec_path


def main() -> None:
    suite, exec_path = parse_args()
    results = run_all(suite, exec_path)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
