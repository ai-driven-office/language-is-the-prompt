#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <suite-id>"
  echo "available suites: all suite_a suite_b suite_c suite_d suite_e suite_f suite_g suite_h suite_i"
  exit 1
fi

SUITE_ID="$1"
EXEC_PATH="${2:-outputs/openai-5-4-medium-adaptive.native-fixed.exec.jsonl}"

case "$SUITE_ID" in
  all|suite_a|suite_b|suite_c|suite_d|suite_e|suite_f|suite_g|suite_h|suite_i)
    python3 scripts/elixir_research_suite_manager.py "$SUITE_ID" "$EXEC_PATH"
    ;;
  *)
    echo "unknown suite: $SUITE_ID"
    echo "available suites: all suite_a suite_b suite_c suite_d suite_e suite_f suite_g suite_h suite_i"
    exit 1
    ;;
esac
