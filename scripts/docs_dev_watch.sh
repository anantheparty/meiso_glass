#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL="${DOCS_WATCH_INTERVAL:-10}"

while true; do
  "$ROOT/scripts/docs_dev_ensure.sh" >/dev/null
  sleep "$INTERVAL"
done
