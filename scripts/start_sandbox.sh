#!/usr/bin/env bash
set -euo pipefail

IMAGE="${SANDBOX_IMAGE:-hunyuansandbox/multi-language-sandbox:v1}"
NAME="${SANDBOX_CONTAINER_NAME:-sandbox-service}"
PORT="${SANDBOX_PORT:-8080}"

if docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Sandbox container '$NAME' is already running."
else
  if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
    docker start "$NAME" >/dev/null
  else
    docker pull "$IMAGE"
    docker run -d \
      --name "$NAME" \
      -p "${PORT}:8080" \
      --cap-add=NET_ADMIN \
      "$IMAGE" >/dev/null
  fi
fi

curl -fsS -X POST "http://localhost:${PORT}/submit" \
  -H "Content-Type: application/json" \
  -d '{"src_uid":"test-001","lang":"python","source_code":"print(\"Hello World\")"}' \
  > /tmp/autocodebench-sandbox-health.json 2>/tmp/autocodebench-sandbox-health.err || true

for _ in $(seq 1 30); do
  if curl -fsS -X POST "http://localhost:${PORT}/submit" \
    -H "Content-Type: application/json" \
    -d '{"src_uid":"test-001","lang":"python","source_code":"print(\"Hello World\")"}' \
    > /tmp/autocodebench-sandbox-health.json 2>/tmp/autocodebench-sandbox-health.err; then
    if rg -q '"exec_outcome"\s*:\s*"PASSED"' /tmp/autocodebench-sandbox-health.json; then
      echo "Sandbox is ready on http://localhost:${PORT}"
      exit 0
    fi
  fi
  sleep 2
done

echo "Sandbox health check failed."
cat /tmp/autocodebench-sandbox-health.err 2>/dev/null || true
cat /tmp/autocodebench-sandbox-health.json 2>/dev/null || true
exit 1
