#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${1:-/home/ubuntu/GovPress_PDF_MD}"
SERVICE_USER="${SUDO_USER:-$(stat -c '%U' "$DEPLOY_DIR")}"
UNIT_TEMPLATE="$DEPLOY_DIR/deploy/vps/systemd/govpress-read-shortener.service"
UNIT_PATH="/etc/systemd/system/govpress-read-shortener.service"
MAP_PATH="$DEPLOY_DIR/config/read_shortlinks.json"
PYTHON_BIN="/usr/bin/python3"
PORT="8091"

if [[ $EUID -ne 0 ]]; then
  echo "run with sudo" >&2
  exit 1
fi

if [[ ! -f "$MAP_PATH" ]]; then
  echo "missing shortlink map: $MAP_PATH" >&2
  exit 1
fi

$PYTHON_BIN "$DEPLOY_DIR/scripts/read_shortener_server.py" --map-file "$MAP_PATH" --validate-only >/dev/null

sed \
  -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" \
  -e "s|__SERVICE_USER__|$SERVICE_USER|g" \
  "$UNIT_TEMPLATE" > "$UNIT_PATH"

systemctl daemon-reload
systemctl enable govpress-read-shortener.service
systemctl restart govpress-read-shortener.service

for _ in 1 2 3 4 5 6 7 8 9 10; do
  status_code="$(curl -sS -o /tmp/govpress-read-shortener-health.txt -w '%{http_code}' http://127.0.0.1:${PORT}/health || true)"
  if [[ "$status_code" == "200" ]]; then
    cat /tmp/govpress-read-shortener-health.txt
    exit 0
  fi
  sleep 2
done

systemctl --no-pager --full status govpress-read-shortener.service || true
journalctl -u govpress-read-shortener.service -n 50 --no-pager || true
exit 1
