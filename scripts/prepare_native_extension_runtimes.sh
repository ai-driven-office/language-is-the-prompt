#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="$ROOT_DIR/tmp/native_runtimes/typescript_effect"

mkdir -p "$RUNTIME_ROOT"
cd "$RUNTIME_ROOT"

if [[ ! -f package.json ]]; then
  npm init -y >/dev/null 2>&1
fi

if [[ ! -x node_modules/.bin/tsx ]]; then
  npm install --silent tsx typescript effect @effect/platform @effect/schema
fi

echo "Prepared TypeScript Effect runtime in $RUNTIME_ROOT"
