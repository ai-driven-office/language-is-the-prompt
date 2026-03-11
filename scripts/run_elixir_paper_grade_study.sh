#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

CONCURRENCY="${ELIXIR_STUDY_CONCURRENCY:-12}"
MIN_CONCURRENCY="${ELIXIR_STUDY_MIN_CONCURRENCY:-12}"
SUITES="${1:-suite_d suite_e suite_f}"
FRESH_FLAG="${ELIXIR_STUDY_FRESH:-0}"

cd "${ROOT_DIR}"

echo "Using python: ${PYTHON_BIN}"
echo "Generating full paper-scale active-suite inputs"
"${PYTHON_BIN}" scripts/elixir_active_ablation_runner.py generate --per-difficulty 0

for suite_id in ${SUITES}; do
  echo "Running ${suite_id}"
  args=(
    scripts/elixir_active_ablation_runner.py
    run
    --suite
    "${suite_id}"
    --concurrency
    "${CONCURRENCY}"
    --min-concurrency
    "${MIN_CONCURRENCY}"
  )
  if [[ "${FRESH_FLAG}" == "1" ]]; then
    args+=(--fresh)
  fi
  "${PYTHON_BIN}" "${args[@]}"
done

echo "Summarizing active suites"
"${PYTHON_BIN}" scripts/elixir_active_ablation_runner.py summarize

echo "Building master summary"
"${PYTHON_BIN}" scripts/build_elixir_research_master_summary.py

echo "Writing paper-grade report"
"${PYTHON_BIN}" scripts/write_elixir_paper_grade_report.py

echo "Done"
