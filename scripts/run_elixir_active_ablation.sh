#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMMAND="${1:-all}"
SUITE="${2:-all}"

python3 scripts/elixir_active_ablation_runner.py "$COMMAND" --suite "$SUITE"
