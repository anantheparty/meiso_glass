#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${DOCS_HOST:-127.0.0.1}"
PORT="${DOCS_PORT:-5173}"
LOG_DIR="${DOCS_LOG_DIR:-${ROOT}/logs}"
LOG_FILE="${DOCS_DEV_LOG:-${LOG_DIR}/docs-dev.log}"
PID_FILE="${DOCS_DEV_PID:-${LOG_DIR}/docs-dev.pid}"
VITEPRESS_BIN="${ROOT}/node_modules/.bin/vitepress"

is_listening() {
  python3 - "$HOST" "$PORT" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.5)
    raise SystemExit(0 if sock.connect_ex((host, port)) == 0 else 1)
PY
}

if is_listening; then
  echo "docs dev server already reachable at http://${HOST}:${PORT}/"
  exit 0
fi

if [[ ! -x "$VITEPRESS_BIN" ]]; then
  echo "missing ${VITEPRESS_BIN}; run npm ci first" >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

(
  cd "$ROOT"
  nohup "$VITEPRESS_BIN" dev docs --host "$HOST" --port "$PORT" >>"$LOG_FILE" 2>&1 &
  echo "$!" >"$PID_FILE"
)

for _ in {1..20}; do
  if is_listening; then
    echo "started docs dev server at http://${HOST}:${PORT}/"
    echo "log: ${LOG_FILE}"
    exit 0
  fi
  sleep 0.25
done

echo "docs dev server did not become reachable; see ${LOG_FILE}" >&2
exit 1
