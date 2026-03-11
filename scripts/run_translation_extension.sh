#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
else
  PYTHON="python3"
fi

if [[ $# -lt 4 ]]; then
  cat <<'EOF'
Usage:
  ./scripts/run_translation_extension.sh <target-template> <target-language> <source-language> <output-prefix> [variant]

Example:
  ./scripts/run_translation_extension.sh gleam gleam python outputs/extensions/gleam-from-python
  ./scripts/run_translation_extension.sh lean4 lean4 python outputs/extensions/lean4-from-python
  ./scripts/run_translation_extension.sh typescript_effect typescript_effect python outputs/extensions/typescript-effect-from-python effect

Environment:
  EXTENSION_INPUT_FILE      default: data/benchmarks/autocodebench.jsonl
  EXTENSION_LIMIT           default: unset (all rows for the selected source language)
  TRANSLATION_OPENAI_MODEL            default: $OPENAI_MODEL or gpt-5.4
  TRANSLATION_OPENAI_REASONING        default: low
  TRANSLATION_OPENAI_MAX_TOKENS       default: 16384
  TRANSLATION_OPENAI_CONCURRENCY      default: $OPENAI_CONCURRENCY or 6
  TRANSLATION_OPENAI_MIN_CONCURRENCY  default: $OPENAI_MIN_CONCURRENCY or 3
EOF
  exit 1
fi

TARGET_TEMPLATE="$1"
TARGET_LANGUAGE="$2"
SOURCE_LANGUAGE="$3"
OUTPUT_PREFIX="$4"
VARIANT="${5:-}"
INPUT_FILE="${EXTENSION_INPUT_FILE:-data/benchmarks/autocodebench.jsonl}"

MESSAGES_FILE="${OUTPUT_PREFIX}.messages.jsonl"
RAW_OUTPUT_FILE="${OUTPUT_PREFIX}.raw.jsonl"
PARSED_OUTPUT_FILE="${OUTPUT_PREFIX}.benchmark.jsonl"

BUILD_ARGS=(
  --input-file "$INPUT_FILE"
  --output-file "$MESSAGES_FILE"
  --target-template "$TARGET_TEMPLATE"
  --target-language "$TARGET_LANGUAGE"
  --source-language "$SOURCE_LANGUAGE"
)

if [[ -n "$VARIANT" ]]; then
  BUILD_ARGS+=(--variant "$VARIANT")
fi
if [[ -n "${EXTENSION_LIMIT:-}" ]]; then
  BUILD_ARGS+=(--limit "$EXTENSION_LIMIT")
fi

"$PYTHON" scripts/build_translation_messages.py \
  "${BUILD_ARGS[@]}"

"$PYTHON" scripts/api_benchmark_runner.py \
  --provider openai \
  --model "${TRANSLATION_OPENAI_MODEL:-${OPENAI_MODEL:-gpt-5.4}}" \
  --input-file "$MESSAGES_FILE" \
  --output-file "$RAW_OUTPUT_FILE" \
  --messages-key messages \
  --question-key question \
  --dedupe-key _translation_source_index \
  --concurrency "${TRANSLATION_OPENAI_CONCURRENCY:-${OPENAI_CONCURRENCY:-6}}" \
  --min-concurrency "${TRANSLATION_OPENAI_MIN_CONCURRENCY:-${OPENAI_MIN_CONCURRENCY:-3}}" \
  --adaptive-concurrency \
  --reasoning-effort "${TRANSLATION_OPENAI_REASONING:-low}" \
  --verbosity low \
  --max-tokens "${TRANSLATION_OPENAI_MAX_TOKENS:-16384}"

"$PYTHON" scripts/extract_translated_benchmark.py \
  --input-file "$RAW_OUTPUT_FILE" \
  --output-file "$PARSED_OUTPUT_FILE"

echo "Wrote:"
echo "  messages: $MESSAGES_FILE"
echo "  raw model output: $RAW_OUTPUT_FILE"
echo "  parsed benchmark rows: $PARSED_OUTPUT_FILE"
