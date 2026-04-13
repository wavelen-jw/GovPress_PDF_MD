#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DEPLOY_DIR=$(cd -- "$SCRIPT_DIR/../.." && pwd)
HOME_DIR="${HOME:-$(getent passwd "$(id -u)" | cut -d: -f6)}"
ENV_PATH="$SCRIPT_DIR/.env"
COMPOSE_PATH="$SCRIPT_DIR/docker-compose.host-proxy.yml"

upsert_env_value() {
  local env_file="$1"
  local key="$2"
  local value="$3"
  python3 - <<'PY' "$env_file" "$key" "$value"
from pathlib import Path
import sys

env_path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = env_path.read_text().splitlines() if env_path.exists() else []
updated = []
seen = False
for line in lines:
    if line.startswith(f"{key}="):
        updated.append(f"{key}={value}")
        seen = True
    else:
        updated.append(line)
if not seen:
    updated.append(f"{key}={value}")
env_path.write_text("\n".join(updated).rstrip() + "\n")
PY
}

render_systemd_unit() {
  local source_path="$1"
  local dest_path="$2"
  local tmp_file
  tmp_file="$(mktemp)"
  sed \
    -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" \
    -e "s|__HOME_DIR__|$HOME_DIR|g" \
    "$source_path" > "$tmp_file"
  sudo cp "$tmp_file" "$dest_path"
  rm -f "$tmp_file"
}

echo "== GovPress host-proxy apply =="
echo "deploy_dir=$DEPLOY_DIR"
echo "home_dir=$HOME_DIR"

sudo -v

upsert_env_value "$ENV_PATH" "GOVPRESS_DEPLOY_MODE" "host_proxy"

render_systemd_unit "$SCRIPT_DIR/systemd/govpress-compose.service" /etc/systemd/system/govpress-compose.service
render_systemd_unit "$SCRIPT_DIR/systemd/govpress-caddy.service" /etc/systemd/system/govpress-caddy.service
render_systemd_unit "$SCRIPT_DIR/systemd/govpress-cloudflared.service" /etc/systemd/system/govpress-cloudflared.service

sudo systemctl daemon-reload
sudo systemctl enable govpress-compose.service govpress-caddy.service govpress-cloudflared.service

docker rm -f govpress-caddy govpress-cloudflared govpress-caddy-host >/dev/null 2>&1 || true

COMPOSE_FILE_OVERRIDE="$COMPOSE_PATH" "$SCRIPT_DIR/bin/compose.sh" up -d --build --remove-orphans api worker

sudo systemctl restart govpress-caddy.service
sudo systemctl restart govpress-cloudflared.service

echo "== Service status =="
sudo systemctl status --no-pager govpress-compose.service govpress-caddy.service govpress-cloudflared.service || true

echo "== Health checks =="
curl -sS http://127.0.0.1:8013/health || true
echo
curl -sS http://127.0.0.1:8080/health || true
echo

if grep -q "api4.govpress.cloud" "$ENV_PATH" 2>/dev/null; then
  curl -i --max-time 10 https://api4.govpress.cloud/health || true
else
  curl -i --max-time 10 https://api4.govpress.cloud/health || true
fi
