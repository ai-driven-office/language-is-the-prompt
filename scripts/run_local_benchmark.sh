#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INPUT_FILE="${BENCHMARK_INPUT_FILE:-data/benchmarks/autocodebench.jsonl}"
OPENAI_LABEL="${OPENAI_LABEL:-OpenAI 5.4 Medium}"
ANTHROPIC_LABEL="${ANTHROPIC_LABEL:-Opus 4.6 Extended}"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.4}"
ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-}"
OPENAI_OUTPUT="${OPENAI_OUTPUT:-outputs/openai-5-4-medium.jsonl}"
ANTHROPIC_OUTPUT="${ANTHROPIC_OUTPUT:-outputs/opus-4-6-extended.jsonl}"
OPENAI_CONCURRENCY="${OPENAI_CONCURRENCY:-12}"
OPENAI_MIN_CONCURRENCY="${OPENAI_MIN_CONCURRENCY:-4}"
ANTHROPIC_CONCURRENCY="${ANTHROPIC_CONCURRENCY:-4}"
OPENAI_REASONING_EFFORT="${OPENAI_REASONING_EFFORT:-medium}"
OPENAI_VERBOSITY="${OPENAI_VERBOSITY:-low}"
OPENAI_MAX_TOKENS="${OPENAI_MAX_TOKENS:-4096}"
OPENAI_MAX_ATTEMPTS="${OPENAI_MAX_ATTEMPTS:-4}"
ANTHROPIC_THINKING_BUDGET="${ANTHROPIC_THINKING_BUDGET:-16000}"
SANDBOX_CONCURRENCY="${SANDBOX_CONCURRENCY:-12}"
SANDBOX_MIN_CONCURRENCY="${SANDBOX_MIN_CONCURRENCY:-3}"
export SANDBOX_CONCURRENCY
export SANDBOX_MIN_CONCURRENCY

./scripts/start_sandbox.sh

if [[ -n "${VERIFY_CANONICAL:-}" ]]; then
  .venv/bin/python call_sandbox.py \
    --input_file "$INPUT_FILE" \
    --output outputs/canonical.exec.jsonl \
    --server_ip localhost \
    --server_port "${SANDBOX_PORT:-8080}" \
    --concurrency "${SANDBOX_CONCURRENCY:-20}" \
    --solution_key canonical_solution
fi

if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  if [[ -z "$OPENAI_MODEL" ]]; then
    echo "Skipping OpenAI run: OPENAI_MODEL is not set."
  else
    .venv/bin/python scripts/api_benchmark_runner.py \
      --provider openai \
      --model "$OPENAI_MODEL" \
      --label "$OPENAI_LABEL" \
      --input-file "$INPUT_FILE" \
      --output-file "$OPENAI_OUTPUT" \
      --adaptive-concurrency \
      --concurrency "$OPENAI_CONCURRENCY" \
      --min-concurrency "$OPENAI_MIN_CONCURRENCY" \
      --reasoning-effort "$OPENAI_REASONING_EFFORT" \
      --verbosity "$OPENAI_VERBOSITY" \
      --max-tokens "$OPENAI_MAX_TOKENS" \
      --max-attempts "$OPENAI_MAX_ATTEMPTS"
    ./scripts/score_benchmark.sh "$OPENAI_OUTPUT"
  fi
else
  echo "Skipping OpenAI run: OPENAI_API_KEY is not set."
fi

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  if [[ -z "$ANTHROPIC_MODEL" ]]; then
    echo "Skipping Anthropic run: ANTHROPIC_MODEL is not set."
  else
    .venv/bin/python scripts/api_benchmark_runner.py \
      --provider anthropic \
      --model "$ANTHROPIC_MODEL" \
      --label "$ANTHROPIC_LABEL" \
      --input-file "$INPUT_FILE" \
      --output-file "$ANTHROPIC_OUTPUT" \
      --concurrency "$ANTHROPIC_CONCURRENCY" \
      --thinking-budget "$ANTHROPIC_THINKING_BUDGET"
    ./scripts/score_benchmark.sh "$ANTHROPIC_OUTPUT"
  fi
else
  echo "Skipping Anthropic run: ANTHROPIC_API_KEY is not set."
fi
