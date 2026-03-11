#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <model-output.jsonl> [scored-output.jsonl]"
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-${INPUT_FILE%.jsonl}.exec.jsonl}"
PORT="${SANDBOX_PORT:-8080}"
CONCURRENCY="${SANDBOX_CONCURRENCY:-20}"
MIN_CONCURRENCY="${SANDBOX_MIN_CONCURRENCY:-4}"

.venv/bin/python call_sandbox.py \
  --input_file "$INPUT_FILE" \
  --output "$OUTPUT_FILE" \
  --server_ip localhost \
  --server_port "$PORT" \
  --concurrency "$CONCURRENCY" \
  --adaptive-concurrency \
  --min-concurrency "$MIN_CONCURRENCY" \
  --solution_key output
