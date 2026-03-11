#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

BENCHMARK_FILE="${ROOT_DIR}/data/explicit_task_factorial/benchmark.jsonl"
CANONICAL_OUTPUT="${ROOT_DIR}/outputs/explicit_task_factorial/canonical.exec.jsonl"
MODEL_OUTPUT="${ROOT_DIR}/outputs/explicit_task_factorial/gpt-5-4-medium.jsonl"
SCORED_OUTPUT="${ROOT_DIR}/outputs/explicit_task_factorial/gpt-5-4-medium.exec.jsonl"

OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.4}"
OPENAI_CONCURRENCY="${OPENAI_CONCURRENCY:-8}"
OPENAI_MIN_CONCURRENCY="${OPENAI_MIN_CONCURRENCY:-4}"
SANDBOX_CONCURRENCY="${SANDBOX_CONCURRENCY:-8}"
SANDBOX_MIN_CONCURRENCY="${SANDBOX_MIN_CONCURRENCY:-3}"
OPENAI_REASONING_EFFORT="${OPENAI_REASONING_EFFORT:-medium}"
OPENAI_VERBOSITY="${OPENAI_VERBOSITY:-low}"
OPENAI_MAX_TOKENS="${OPENAI_MAX_TOKENS:-4096}"

mkdir -p "${ROOT_DIR}/outputs/explicit_task_factorial" "${ROOT_DIR}/results/explicit_task_factorial"

echo "Generating factorial prompt records"
"${PYTHON_BIN}" scripts/build_explicit_task_factorial.py

echo "Building factorial benchmark rows"
"${PYTHON_BIN}" scripts/build_explicit_task_factorial_benchmark.py

echo "Starting sandbox"
./scripts/start_sandbox.sh

echo "Validating canonical solutions"
export ACB_NATIVE_LANGS="${ACB_NATIVE_LANGS:-elixir}"
"${PYTHON_BIN}" call_sandbox.py \
  --input_file "${BENCHMARK_FILE}" \
  --output "${CANONICAL_OUTPUT}" \
  --server_ip localhost \
  --server_port "${SANDBOX_PORT:-8080}" \
  --concurrency "${SANDBOX_CONCURRENCY}" \
  --adaptive-concurrency \
  --min-concurrency "${SANDBOX_MIN_CONCURRENCY}" \
  --solution_key canonical_solution

"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
path = Path("/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/explicit_task_factorial/canonical.exec.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
failed = [row for row in rows if not row.get("success")]
if failed:
    print(f"Canonical validation failed for {len(failed)} rows.")
    for row in failed[:10]:
        original = row.get("original_data", {})
        print(original.get("experiment_id"), row.get("language"))
    raise SystemExit(1)
print(f"Canonical validation passed for {len(rows)} rows.")
PY

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is not set."
  exit 1
fi

echo "Running GPT-5.4 Medium on explicit task factorial study"
"${PYTHON_BIN}" scripts/api_benchmark_runner.py \
  --provider openai \
  --model "${OPENAI_MODEL}" \
  --label "GPT-5.4 Medium Explicit Task Factorial" \
  --input-file "${BENCHMARK_FILE}" \
  --output-file "${MODEL_OUTPUT}" \
  --question-key question \
  --dedupe-key experiment_id \
  --adaptive-concurrency \
  --concurrency "${OPENAI_CONCURRENCY}" \
  --min-concurrency "${OPENAI_MIN_CONCURRENCY}" \
  --reasoning-effort "${OPENAI_REASONING_EFFORT}" \
  --verbosity "${OPENAI_VERBOSITY}" \
  --max-tokens "${OPENAI_MAX_TOKENS}"

echo "Scoring model outputs"
ACB_NATIVE_LANGS="${ACB_NATIVE_LANGS}" SANDBOX_CONCURRENCY="${SANDBOX_CONCURRENCY}" SANDBOX_MIN_CONCURRENCY="${SANDBOX_MIN_CONCURRENCY}" \
  ./scripts/score_benchmark.sh "${MODEL_OUTPUT}" "${SCORED_OUTPUT}"

echo "Summarizing results"
"${PYTHON_BIN}" scripts/summarize_explicit_task_factorial.py

echo "Done"
