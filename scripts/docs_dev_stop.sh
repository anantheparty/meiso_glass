#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${DOCS_DEV_PID:-${ROOT}/logs/docs-dev.pid}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "no docs dev pid file at ${PID_FILE}"
  exit 0
fi

PID="$(cat "$PID_FILE")"

if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "stopped docs dev server pid ${PID}"
else
  echo "docs dev pid ${PID:-<empty>} is not running"
fi

rm -f "$PID_FILE"
