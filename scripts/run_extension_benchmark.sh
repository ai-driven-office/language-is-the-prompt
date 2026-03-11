#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -lt 4 ]]; then
  cat <<'EOF'
Usage:
  ./scripts/run_extension_benchmark.sh <target-template> <target-language> <source-language> <output-prefix> [variant]

Examples:
  ./scripts/run_extension_benchmark.sh gleam gleam python outputs/extensions/gleam-from-python
  ./scripts/run_extension_benchmark.sh lean4 lean4 python outputs/extensions/lean4-from-python
  ./scripts/run_extension_benchmark.sh typescript_effect typescript_effect python outputs/extensions/typescript-effect-from-python effect

Environment:
  OPENAI_MODEL                 default: gpt-5.4
  OPENAI_REASONING             default: medium (solve stage)
  OPENAI_MAX_TOKENS            default: 8192 (solve stage)
  OPENAI_CONCURRENCY           default: 6
  OPENAI_MIN_CONCURRENCY       default: 3
  TRANSLATION_OPENAI_REASONING default: low (translation stage)
  EXTENSION_SOLVE_CONCURRENCY  default: 6
  EXTENSION_SCORE_CONCURRENCY  default: 4
  EXTENSION_REPAIR_ROUNDS      default: 1 for lean4, else 0
EOF
  exit 1
fi

TARGET_TEMPLATE="$1"
TARGET_LANGUAGE="$2"
SOURCE_LANGUAGE="$3"
OUTPUT_PREFIX="$4"
VARIANT="${5:-}"

if [[ -x "$ROOT_DIR/.venv/bin/python3" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python3"
else
  PYTHON_BIN="python3"
fi

if [[ "$TARGET_LANGUAGE" == "typescript_effect" ]]; then
  ./scripts/prepare_native_extension_runtimes.sh
fi

if [[ "$TARGET_LANGUAGE" == "lean4" ]]; then
  export PATH="$HOME/.elan/bin:$PATH"
fi

if [[ -z "${TRANSLATION_OPENAI_REASONING:-}" ]]; then
  case "$TARGET_LANGUAGE" in
    gleam|lean4)
      export TRANSLATION_OPENAI_REASONING="high"
      ;;
  esac
fi

if [[ -z "${TRANSLATION_OPENAI_MAX_TOKENS:-}" ]]; then
  case "$TARGET_LANGUAGE" in
    gleam|lean4)
      export TRANSLATION_OPENAI_MAX_TOKENS="32768"
      ;;
  esac
fi

OPENAI_CONCURRENCY="${OPENAI_CONCURRENCY:-6}" \
OPENAI_MIN_CONCURRENCY="${OPENAI_MIN_CONCURRENCY:-3}" \
./scripts/run_translation_extension.sh \
  "$TARGET_TEMPLATE" \
  "$TARGET_LANGUAGE" \
  "$SOURCE_LANGUAGE" \
  "$OUTPUT_PREFIX" \
  ${VARIANT:+"$VARIANT"}

BENCHMARK_FILE="${OUTPUT_PREFIX}.benchmark.jsonl"
CANONICAL_EXEC_FILE="${OUTPUT_PREFIX}.benchmark.canonical.exec.jsonl"
VALID_BENCHMARK_FILE="${OUTPUT_PREFIX}.benchmark.valid.jsonl"
SOLUTIONS_FILE="${OUTPUT_PREFIX}.solutions.jsonl"
EXEC_FILE="${OUTPUT_PREFIX}.solutions.exec.jsonl"

REPAIR_ROUNDS="${EXTENSION_REPAIR_ROUNDS:-}"
if [[ -z "$REPAIR_ROUNDS" ]]; then
  if [[ "$TARGET_LANGUAGE" == "lean4" ]]; then
    REPAIR_ROUNDS=1
  else
    REPAIR_ROUNDS=0
  fi
fi

"$PYTHON_BIN" call_sandbox.py \
  --input_file "$BENCHMARK_FILE" \
  --output "$CANONICAL_EXEC_FILE" \
  --server_ip localhost \
  --server_port 8080 \
  --concurrency "${EXTENSION_SCORE_CONCURRENCY:-4}" \
  --solution_key canonical_solution \
  --native-langs "$TARGET_LANGUAGE"

CURRENT_BENCHMARK_FILE="$BENCHMARK_FILE"
CURRENT_EXEC_FILE="$CANONICAL_EXEC_FILE"

for ((repair_round = 1; repair_round <= REPAIR_ROUNDS; repair_round++)); do
  REPAIR_MESSAGES_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.messages.jsonl"
  REPAIR_RAW_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.raw.jsonl"
  REPAIR_BENCHMARK_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.jsonl"
  REPAIR_EXEC_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.exec.jsonl"
  REPAIR_VALID_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.valid.jsonl"
  MERGED_BENCHMARK_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.merged.jsonl"
  MERGED_EXEC_FILE="${OUTPUT_PREFIX}.benchmark.repair${repair_round}.merged.exec.jsonl"

  "$PYTHON_BIN" scripts/build_translation_repair_messages.py \
    --input-file "$CURRENT_EXEC_FILE" \
    --output-file "$REPAIR_MESSAGES_FILE" \
    --language "$TARGET_LANGUAGE"

  if [[ ! -s "$REPAIR_MESSAGES_FILE" ]]; then
    break
  fi

  "$PYTHON_BIN" scripts/api_benchmark_runner.py \
    --provider openai \
    --model "${TRANSLATION_OPENAI_MODEL:-${OPENAI_MODEL:-gpt-5.4}}" \
    --input-file "$REPAIR_MESSAGES_FILE" \
    --output-file "$REPAIR_RAW_FILE" \
    --messages-key messages \
    --question-key question \
    --dedupe-key _translation_source_index \
    --concurrency "${TRANSLATION_OPENAI_CONCURRENCY:-${OPENAI_CONCURRENCY:-6}}" \
    --min-concurrency "${TRANSLATION_OPENAI_MIN_CONCURRENCY:-${OPENAI_MIN_CONCURRENCY:-3}}" \
    --adaptive-concurrency \
    --reasoning-effort "${TRANSLATION_OPENAI_REASONING:-low}" \
    --verbosity low \
    --max-tokens "${TRANSLATION_OPENAI_MAX_TOKENS:-16384}"

  "$PYTHON_BIN" scripts/extract_translated_benchmark.py \
    --input-file "$REPAIR_RAW_FILE" \
    --output-file "$REPAIR_BENCHMARK_FILE"

  "$PYTHON_BIN" call_sandbox.py \
    --input_file "$REPAIR_BENCHMARK_FILE" \
    --output "$REPAIR_EXEC_FILE" \
    --server_ip localhost \
    --server_port 8080 \
    --concurrency "${EXTENSION_SCORE_CONCURRENCY:-4}" \
    --solution_key canonical_solution \
    --native-langs "$TARGET_LANGUAGE"

  "$PYTHON_BIN" scripts/filter_successful_exec_rows.py \
    --input-file "$REPAIR_EXEC_FILE" \
    --output-file "$REPAIR_VALID_FILE"

  "$PYTHON_BIN" scripts/merge_benchmark_rows.py \
    --base "$CURRENT_BENCHMARK_FILE" \
    --replacement "$REPAIR_VALID_FILE" \
    --output "$MERGED_BENCHMARK_FILE"

  "$PYTHON_BIN" scripts/merge_exec_results.py \
    --base "$CURRENT_EXEC_FILE" \
    --replacement "$REPAIR_EXEC_FILE" \
    --output "$MERGED_EXEC_FILE"

  CURRENT_BENCHMARK_FILE="$MERGED_BENCHMARK_FILE"
  CURRENT_EXEC_FILE="$MERGED_EXEC_FILE"
done

"$PYTHON_BIN" scripts/filter_successful_exec_rows.py \
  --input-file "$CURRENT_EXEC_FILE" \
  --output-file "$VALID_BENCHMARK_FILE"

"$PYTHON_BIN" scripts/api_benchmark_runner.py \
  --provider openai \
  --model "${OPENAI_MODEL:-gpt-5.4}" \
  --input-file "$VALID_BENCHMARK_FILE" \
  --output-file "$SOLUTIONS_FILE" \
  --question-key question \
  --messages-key messages \
  --dedupe-key question \
  --concurrency "${EXTENSION_SOLVE_CONCURRENCY:-6}" \
  --min-concurrency "${OPENAI_MIN_CONCURRENCY:-3}" \
  --adaptive-concurrency \
  --reasoning-effort "${OPENAI_REASONING:-medium}" \
  --verbosity low \
  --max-tokens "${OPENAI_MAX_TOKENS:-8192}"

"$PYTHON_BIN" call_sandbox.py \
  --input_file "$SOLUTIONS_FILE" \
  --output "$EXEC_FILE" \
  --server_ip localhost \
  --server_port 8080 \
  --concurrency "${EXTENSION_SCORE_CONCURRENCY:-4}" \
  --solution_key output \
  --native-langs "$TARGET_LANGUAGE"

echo "Wrote:"
echo "  benchmark: $BENCHMARK_FILE"
echo "  canonical exec: $CANONICAL_EXEC_FILE"
echo "  validated benchmark: $VALID_BENCHMARK_FILE"
echo "  solutions: $SOLUTIONS_FILE"
echo "  scored: $EXEC_FILE"
