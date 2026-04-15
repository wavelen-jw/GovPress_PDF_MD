#!/usr/bin/env bash
set -euo pipefail

echo "=== govpress remote diagnostics ==="
echo "remote_host=$(hostname)"
echo "remote_user=$(whoami)"
echo "deploy_dir=${DEPLOY_DIR}"
echo "target_branch=${BRANCH}"
echo "deploy_mode=${DEPLOY_MODE:-compose_proxy}"

git -C "$DEPLOY_DIR" fetch origin
# Deploy targets are treated as disposable working trees.
# Remove local modifications and untracked build artifacts before switching refs,
# but preserve runtime data, venvs, and existing env files.
git -C "$DEPLOY_DIR" reset --hard
git -C "$DEPLOY_DIR" clean -fdx \
  -e .venv/ \
  -e storage/ \
  -e deploy/wsl/.env \
  -e deploy/wsl/config/ \
  -e deploy/wsl/data/ \
  -e deploy/vps/.env \
  -e deploy/vps/data/
git -C "$DEPLOY_DIR" checkout "$BRANCH"
git -C "$DEPLOY_DIR" reset --hard "origin/$BRANCH"

echo "git_branch=$(git -C "$DEPLOY_DIR" branch --show-current)"
echo "git_head=$(git -C "$DEPLOY_DIR" rev-parse HEAD)"
echo "target_sha=$(git -C "$DEPLOY_DIR" rev-parse HEAD)"
echo "git_origin=$(git -C "$DEPLOY_DIR" remote get-url origin)"
HOME_DIR="${HOME:-$(getent passwd $(id -u) | cut -d: -f6)}"

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

run_compose() {
  if [ -x "$DEPLOY_DIR/deploy/wsl/bin/compose.sh" ]; then
    COMPOSE_FILE_OVERRIDE="$COMPOSE_PATH" "$DEPLOY_DIR/deploy/wsl/bin/compose.sh" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_PATH" "$@"
  else
    docker compose -f "$COMPOSE_PATH" "$@"
  fi
}

cleanup_host_proxy_orphans() {
  docker rm -f govpress-caddy-host govpress-caddy govpress-cloudflared >/dev/null 2>&1 || true
  echo "host_proxy_orphan_cleanup=1"
}

cleanup_host_proxy_port_conflicts() {
  local pids
  pids="$(
    (sudo ss -ltnp 'sport = :8080' 2>/dev/null || true) \
      | sed -n 's/.*users:(("docker-proxy",pid=\([0-9]\+\).*/\1/p' \
      | sort -u
  )"
  if [ -z "$pids" ]; then
    echo "host_proxy_port_conflict_cleanup=0"
    return
  fi
  echo "host_proxy_port_conflict_pids=$pids"
  for pid in $pids; do
    sudo kill "$pid" >/dev/null 2>&1 || true
  done
  sleep 1
  echo "host_proxy_port_conflict_cleanup=1"
}

cleanup_split_edge_orphans() {
  docker rm -f govpress-cloudflared >/dev/null 2>&1 || true
  echo "split_edge_orphan_cleanup=1"
}

require_passwordless_sudo() {
  sudo -n /usr/bin/systemctl daemon-reload >/dev/null 2>&1 || {
    echo "passwordless sudo is required for ${DEPLOY_MODE}" >&2
    exit 1
  }
}

install_split_edge_services() {
  require_passwordless_sudo
  render_systemd_unit "$DEPLOY_DIR/deploy/wsl/systemd/govpress-compose.service" /etc/systemd/system/govpress-compose.service
  render_systemd_unit "$DEPLOY_DIR/deploy/wsl/systemd/govpress-cloudflared.service" /etc/systemd/system/govpress-cloudflared.service
  sudo systemctl daemon-reload
}

render_systemd_unit() {
  local source_path="$1"
  local dest_path="$2"
  sed \
    -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" \
    -e "s|__HOME_DIR__|$HOME_DIR|g" \
    "$source_path" | sudo tee "$dest_path" >/dev/null
}

install_host_proxy_services() {
  require_passwordless_sudo
  render_systemd_unit "$DEPLOY_DIR/deploy/wsl/systemd/govpress-compose.service" /etc/systemd/system/govpress-compose.service
  render_systemd_unit "$DEPLOY_DIR/deploy/wsl/systemd/govpress-caddy.service" /etc/systemd/system/govpress-caddy.service
  render_systemd_unit "$DEPLOY_DIR/deploy/wsl/systemd/govpress-cloudflared.service" /etc/systemd/system/govpress-cloudflared.service
  sudo systemctl daemon-reload
}

restart_host_proxy_edge() {
  require_passwordless_sudo
  sudo pkill -f 'cloudflared tunnel' >/dev/null 2>&1 || true
  sleep 1
  sudo systemctl enable govpress-caddy.service
  sudo systemctl enable govpress-cloudflared.service
  sudo systemctl restart govpress-caddy.service
  sudo systemctl restart govpress-cloudflared.service
  sudo systemctl status --no-pager govpress-caddy.service || true
  sudo systemctl status --no-pager govpress-cloudflared.service || true
  sudo journalctl -u govpress-caddy.service -n 30 --no-pager || true
  sudo journalctl -u govpress-cloudflared.service -n 30 --no-pager || true
}

restart_split_edge_tunnel() {
  require_passwordless_sudo
  sudo systemctl enable govpress-cloudflared.service
  sudo systemctl restart govpress-cloudflared.service
  sudo systemctl status --no-pager govpress-cloudflared.service || true
  sudo journalctl -u govpress-cloudflared.service -n 30 --no-pager || true
}

emit_compose_diagnostics() {
  echo "=== compose diagnostics ==="
  if [ -n "${COMPOSE_FILE:-}" ]; then
    echo "compose_file=$COMPOSE_FILE"
    echo "deploy_mode=${DEPLOY_MODE:-compose_proxy}"
    run_compose ps || true
    run_compose logs --tail=100 api worker caddy cloudflared || true
  fi
  echo "=== host port diagnostics ==="
  ss -ltnp | grep ':8080' || true
  echo "=== systemd diagnostics ==="
  sudo systemctl status --no-pager govpress-compose.service 2>/dev/null || true
  sudo systemctl status --no-pager govpress-caddy.service 2>/dev/null || true
  sudo systemctl status --no-pager govpress-cloudflared.service 2>/dev/null || true
  echo "=== health probe diagnostics ==="
  curl -i --max-time 10 "$HEALTHCHECK_URL" || true
  echo "=== container diagnostics ==="
  docker inspect --format 'name={{.Name}} state={{.State.Status}} exit={{.State.ExitCode}} error={{.State.Error}}' govpress-api govpress-worker govpress-caddy govpress-caddy-host govpress-cloudflared 2>/dev/null || true
}

trap 'emit_compose_diagnostics' ERR

# Keep deploy-time cache eviction explicit so converter upgrades do not keep
# serving stale markdown/results from a previous engine build.
# Preserve the per-day catalog cache so recent-date status checks do not cold-hit
# the upstream provider immediately after every deploy.
rm -f \
  "$DEPLOY_DIR"/storage/results/*.md \
  "$DEPLOY_DIR/deploy/wsl/data/storage/results/"*.md \
  "$DEPLOY_DIR/deploy/vps/data/storage/results/"*.md \
  "$DEPLOY_DIR/storage/policy_briefing_cache/index.json" \
  "$DEPLOY_DIR"/storage/policy_briefing_cache/originals/* \
  "$DEPLOY_DIR/deploy/wsl/data/storage/policy_briefing_cache/index.json" \
  "$DEPLOY_DIR"/deploy/wsl/data/storage/policy_briefing_cache/originals/* \
  "$DEPLOY_DIR/deploy/vps/data/storage/policy_briefing_cache/index.json" \
  "$DEPLOY_DIR"/deploy/vps/data/storage/policy_briefing_cache/originals/* \
  2>/dev/null || true
echo "converter_cache_reset=results_and_policy_briefing_cache"

if [ -n "${COMPOSE_FILE:-}" ]; then
  COMPOSE_PATH="$DEPLOY_DIR/$COMPOSE_FILE"
  ENV_PATH="$(dirname "$COMPOSE_PATH")/.env"
  restart_tunnel_after_compose=0
  if [ ! -f "$ENV_PATH" ]; then
    if docker inspect govpress-api >/dev/null 2>&1; then
      mkdir -p "$(dirname "$ENV_PATH")"
      docker inspect govpress-api --format '{{range .Config.Env}}{{println .}}{{end}}' \
        | grep -E '^(GOVPRESS_|EXPO_PUBLIC_|CLOUDFLARE_TUNNEL_TOKEN=)' \
        > "$ENV_PATH"
    elif [ -f "${ENV_PATH}.example" ]; then
      cp "${ENV_PATH}.example" "$ENV_PATH"
    fi
  fi
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" "$CONVERTER_SPEC"
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "0"
  fi
  if [ -n "${CONVERTER_MIN_VERSION:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_MIN_VERSION" "$CONVERTER_MIN_VERSION"
  fi
  if [ -n "${ADMIN_API_KEY:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_ADMIN_API_KEY" "$ADMIN_API_KEY"
  fi
  if [ -n "${POLICY_BRIEFING_SERVICE_KEY:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_POLICY_BRIEFING_SERVICE_KEY" "$POLICY_BRIEFING_SERVICE_KEY"
    upsert_env_value "$ENV_PATH" "GOVPRESS_ALLOW_DEFAULT_POLICY_BRIEFING_SERVICE_KEY_FALLBACK" "0"
  fi
  if [ "${DEPLOY_MODE:-compose_proxy}" = "host_proxy" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_DEPLOY_MODE" "host_proxy"
    install_host_proxy_services
    cleanup_host_proxy_orphans
    cleanup_host_proxy_port_conflicts
    restart_tunnel_after_compose=2
    echo "host_proxy_tunnel_origin=http://127.0.0.1:8080"
    echo "host_proxy_caddy_unit=govpress-caddy.service"
    echo "host_proxy_cloudflared_unit=govpress-cloudflared.service"
    run_compose up -d --build --remove-orphans api worker
  elif [ "${DEPLOY_MODE:-compose_proxy}" = "split_edge" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_DEPLOY_MODE" "split_edge"
    install_split_edge_services
    cleanup_split_edge_orphans
    restart_tunnel_after_compose=1
    echo "split_edge_tunnel_origin=http://127.0.0.1:8080"
    echo "split_edge_cloudflared_unit=govpress-cloudflared.service"
    run_compose up -d --build --remove-orphans api worker caddy
  else
    run_compose up -d --build --remove-orphans
  fi
  if [ "$restart_tunnel_after_compose" = "1" ]; then
    restart_split_edge_tunnel
  elif [ "$restart_tunnel_after_compose" = "2" ]; then
    restart_host_proxy_edge
  fi
  run_compose ps
  sleep 3
else
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  ENV_PATH="$DEPLOY_DIR/deploy/vps/.env"
  mkdir -p "$(dirname "$ENV_PATH")"
  touch "$ENV_PATH"
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" "$CONVERTER_SPEC"
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "0"
  fi
  if [ -n "${CONVERTER_MIN_VERSION:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_MIN_VERSION" "$CONVERTER_MIN_VERSION"
  fi
  if [ ! -x "$DEPLOY_DIR/.venv/bin/python" ]; then
    python3 -m venv "$DEPLOY_DIR/.venv"
  fi
  "$DEPLOY_DIR/.venv/bin/python" -m pip install -U pip -q
  "$DEPLOY_DIR/.venv/bin/python" -m pip install -r "$DEPLOY_DIR/requirements.txt" -q
  "$DEPLOY_DIR/.venv/bin/python" -m pip install -U opendataloader-pdf -q
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    "$DEPLOY_DIR/.venv/bin/python" -m pip install "$CONVERTER_SPEC" -q
  fi
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    if [ -n "${CONVERTER_MIN_VERSION:-}" ]; then
      "$DEPLOY_DIR/.venv/bin/python" "$DEPLOY_DIR/scripts/check_converter_runtime.py" \
        --require-private-engine \
        --min-version "$CONVERTER_MIN_VERSION"
    else
      "$DEPLOY_DIR/.venv/bin/python" "$DEPLOY_DIR/scripts/check_converter_runtime.py" --require-private-engine
    fi
  fi
  systemctl --user restart "$SERVICE"
  sleep 3
fi

# WSL rebuilds can take noticeably longer than VPS restarts.
health_code=""
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  health_code="$(curl -sS -o /tmp/govpress-health.txt -w '%{http_code}' "$HEALTHCHECK_URL" || true)"
  echo "health_probe_attempt=${attempt} code=${health_code:-curl_failed}"
  if [ "$health_code" = "200" ]; then
    break
  fi
  sleep 3
done
echo "health_probe_code=$health_code"
test "$health_code" = "200"
if [ "${RUN_POLICY_PROBE:-1}" = "1" ]; then
  policy_probe_header=()
  if [ -n "${ENV_PATH:-}" ] && [ -f "$ENV_PATH" ]; then
    api_key="$(sed -n 's/^GOVPRESS_API_KEY=//p' "$ENV_PATH" | tail -n1)"
    if [ -n "$api_key" ]; then
      policy_probe_header=(-H "x-api-key: $api_key")
    fi
  fi
  echo "policy_probe_code=$(curl -sS -o /tmp/govpress-policy.txt -w '%{http_code}' "${policy_probe_header[@]}" 'http://127.0.0.1:8080/v1/policy-briefings/today?date=2026-04-08' || true)"
  echo "policy_probe_body=$(head -c 200 /tmp/govpress-policy.txt | tr '\n' ' ' || true)"
fi
echo "deploy-complete"
