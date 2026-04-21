#!/usr/bin/env bash
set -euo pipefail

echo "=== govpress remote diagnostics ==="
echo "remote_host=$(hostname)"
echo "remote_user=$(whoami)"
echo "deploy_dir=${DEPLOY_DIR}"
echo "target_branch=${BRANCH}"
echo "requested_target_sha=${TARGET_SHA:-}"
echo "deploy_mode=${DEPLOY_MODE:-compose_proxy}"

if [ -n "${TARGET_SHA:-}" ]; then
  git -C "$DEPLOY_DIR" fetch origin "$TARGET_SHA" || git -C "$DEPLOY_DIR" fetch origin
else
  git -C "$DEPLOY_DIR" fetch origin
fi
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
if [ -n "${TARGET_SHA:-}" ]; then
  git -C "$DEPLOY_DIR" checkout --detach "$TARGET_SHA"
  git -C "$DEPLOY_DIR" reset --hard "$TARGET_SHA"
else
  git -C "$DEPLOY_DIR" checkout "$BRANCH"
  git -C "$DEPLOY_DIR" reset --hard "origin/$BRANCH"
fi

echo "git_branch=$(git -C "$DEPLOY_DIR" branch --show-current)"
echo "git_head=$(git -C "$DEPLOY_DIR" rev-parse HEAD)"
echo "target_sha=${TARGET_SHA:-$(git -C "$DEPLOY_DIR" rev-parse HEAD)}"
echo "git_origin=$(git -C "$DEPLOY_DIR" remote get-url origin)"
HOME_DIR="${HOME:-$(getent passwd $(id -u) | cut -d: -f6)}"
CONVERTER_VERSION_FILE="$DEPLOY_DIR/deploy/converter.version"
CONVERTER_SPEC_RESOLVER="$DEPLOY_DIR/deploy/common/resolve_converter_spec.py"

normalize_converter_spec() {
  if [ -z "${CONVERTER_SPEC:-}" ]; then
    return
  fi
  if [ ! -f "$CONVERTER_VERSION_FILE" ] || [ ! -f "$CONVERTER_SPEC_RESOLVER" ]; then
    return
  fi
  CONVERTER_SPEC="$(python3 "$CONVERTER_SPEC_RESOLVER" \
    --spec "$CONVERTER_SPEC" \
    --version-file "$CONVERTER_VERSION_FILE")"
  echo "converter_version=$(cat "$CONVERTER_VERSION_FILE")"
}

normalize_converter_spec

if [ "${CONVERTER_SPEC:-}" = "-" ]; then
  CONVERTER_SPEC=""
fi

normalize_env_placeholder_spec() {
  local env_file="$1"
  [ -f "$env_file" ] || return 0
  python3 - <<'PY' "$env_file"
from pathlib import Path
import sys

env_path = Path(sys.argv[1])
lines = env_path.read_text(encoding="utf-8").splitlines()
updated = []
changed = False
for line in lines:
    if line.startswith("GOVPRESS_CONVERTER_SPEC=") and line.split("=", 1)[1].strip() == "-":
        updated.append("GOVPRESS_CONVERTER_SPEC=")
        changed = True
    else:
        updated.append(line)
if changed:
    env_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
PY
}

ensure_converter_checkout() {
  local converter_root="${GOV_MD_CONVERTER_ROOT:-$(cd "$DEPLOY_DIR/.." && pwd)/gov-md-converter}"
  local parse_output
  local repo_url=""
  local repo_ref=""

  if [ -z "${CONVERTER_SPEC:-}" ]; then
    echo "converter_checkout=skipped_no_spec"
    return
  fi

  parse_output="$(python3 - <<'PY' "${CONVERTER_SPEC}"
import sys
spec = sys.argv[1].strip()
if spec.startswith("git+"):
    spec = spec[4:]
repo = spec
ref = ""
marker = ".git@"
idx = spec.rfind(marker)
if idx != -1:
    repo = spec[: idx + 4]
    ref = spec[idx + len(marker):]
print(repo)
print(ref)
PY
)"
  repo_url="$(printf '%s\n' "$parse_output" | sed -n '1p')"
  repo_ref="$(printf '%s\n' "$parse_output" | sed -n '2p')"
  if [ -z "$repo_url" ]; then
    echo "converter_checkout=skipped_parse_error"
    return
  fi

  if [ ! -d "$converter_root/.git" ]; then
    rm -rf "$converter_root"
    git clone "$repo_url" "$converter_root"
  fi
  git -C "$converter_root" fetch --tags origin
  if [ -n "$repo_ref" ]; then
    git -C "$converter_root" checkout -f "$repo_ref"
  else
    git -C "$converter_root" checkout -f origin/main
  fi
  echo "converter_checkout_root=$converter_root"
  echo "converter_checkout_ref=${repo_ref:-origin/main}"
}

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

build_dashboard_assets_compose() {
  local converter_root="${GOV_MD_CONVERTER_ROOT:-/gov-md-converter}"
  local dashboard_root="${GOVPRESS_QC_EXPORT_ROOT:-/gov-md-converter/exports/policy_briefing_qc}"
  local curated_root="${GOVPRESS_CURATED_QC_ROOT:-/gov-md-converter/tests/qc_samples}"
  docker exec -u "$(id -u):$(id -g)" govpress-api python - "$converter_root" "$dashboard_root" "$dashboard_root/dashboard/index.html" "$dashboard_root/dashboard/dashboard.json" "$curated_root" <<'PY'
from pathlib import Path
import sys

converter_root = Path(sys.argv[1])
sys.path.insert(0, str(converter_root / "src"))
from qc_dashboard import write_dashboard

root = Path(sys.argv[2])
output_html = Path(sys.argv[3])
output_json = Path(sys.argv[4])
curated_root = Path(sys.argv[5]) if len(sys.argv) > 5 and Path(sys.argv[5]).exists() else None
write_dashboard(root, output_html=output_html, output_json=output_json, curated_root=curated_root)
print(f"dashboard_html={output_html}")
print(f"dashboard_json={output_json}")
PY
}

build_dashboard_assets_baremetal() {
  local converter_root="${GOV_MD_CONVERTER_ROOT:-$(cd "$DEPLOY_DIR/.." && pwd)/gov-md-converter}"
  local dashboard_root="${GOVPRESS_QC_EXPORT_ROOT:-$converter_root/exports/policy_briefing_qc}"
  local curated_root="${GOVPRESS_CURATED_QC_ROOT:-$converter_root/tests/qc_samples}"
  "$DEPLOY_DIR/.venv/bin/python" - "$converter_root" "$dashboard_root" "$dashboard_root/dashboard/index.html" "$dashboard_root/dashboard/dashboard.json" "$curated_root" <<'PY'
from pathlib import Path
import sys

converter_root = Path(sys.argv[1])
sys.path.insert(0, str(converter_root / "src"))
from qc_dashboard import write_dashboard

root = Path(sys.argv[2])
output_html = Path(sys.argv[3])
output_json = Path(sys.argv[4])
curated_root = Path(sys.argv[5]) if len(sys.argv) > 5 and Path(sys.argv[5]).exists() else None
write_dashboard(root, output_html=output_html, output_json=output_json, curated_root=curated_root)
print(f"dashboard_html={output_html}")
print(f"dashboard_json={output_json}")
PY
}

verify_dashboard_assets() {
  local dashboard_root="$1"
  local html_path="$dashboard_root/dashboard/index.html"
  local json_path="$dashboard_root/dashboard/dashboard.json"
  test -s "$html_path"
  test -s "$json_path"
  echo "dashboard_html=$html_path"
  echo "dashboard_json=$json_path"
}

build_and_verify_dashboard_assets() {
  local mode="$1"
  local dashboard_root="$2"
  if [ "$mode" = "compose" ]; then
    if ! build_dashboard_assets_compose; then
      echo "dashboard_build_status=failed"
      return 0
    fi
  else
    if ! build_dashboard_assets_baremetal; then
      echo "dashboard_build_status=failed"
      return 0
    fi
  fi
  if ! verify_dashboard_assets "$dashboard_root"; then
    echo "dashboard_verify_status=failed"
    return 0
  fi
}

run_host_proxy_compose_up() {
  local log_file="${1:-/tmp/govpress-compose-up.log}"
  local build_log="${log_file}.build"
  local attempt
  run_compose build api worker >"$build_log" 2>&1
  cat "$build_log"
  for attempt in 1 2 3; do
    host_proxy_stage_backups
    cleanup_host_proxy_port_conflicts
    if run_compose up -d --no-build --remove-orphans api worker >"$log_file" 2>&1; then
      cat "$log_file"
      return 0
    fi
    cat "$log_file"
    host_proxy_restore_backups
    if ! grep -q "ports are not available" "$log_file"; then
      return 1
    fi
    sleep 5
  done
  return 1
}

cleanup_host_proxy_orphans() {
  docker rm -f govpress-caddy-host govpress-caddy govpress-cloudflared >/dev/null 2>&1 || true
  echo "host_proxy_orphan_cleanup=1"
}

HOST_PROXY_BACKUP_ACTIVE=0
HOST_PROXY_API_BACKUP=""
HOST_PROXY_WORKER_BACKUP=""

host_proxy_stage_backups() {
  local suffix
  suffix="$(date +%s)-$$"
  HOST_PROXY_BACKUP_ACTIVE=1
  HOST_PROXY_API_BACKUP=""
  HOST_PROXY_WORKER_BACKUP=""
  if docker inspect govpress-api >/dev/null 2>&1; then
    HOST_PROXY_API_BACKUP="govpress-api-backup-${suffix}"
    docker rename govpress-api "$HOST_PROXY_API_BACKUP"
    docker stop "$HOST_PROXY_API_BACKUP" >/dev/null 2>&1 || true
  fi
  if docker inspect govpress-worker >/dev/null 2>&1; then
    HOST_PROXY_WORKER_BACKUP="govpress-worker-backup-${suffix}"
    docker rename govpress-worker "$HOST_PROXY_WORKER_BACKUP"
    docker stop "$HOST_PROXY_WORKER_BACKUP" >/dev/null 2>&1 || true
  fi
  echo "host_proxy_api_backup=${HOST_PROXY_API_BACKUP:-none}"
  echo "host_proxy_worker_backup=${HOST_PROXY_WORKER_BACKUP:-none}"
}

host_proxy_restore_backups() {
  if [ "${HOST_PROXY_BACKUP_ACTIVE}" != "1" ]; then
    return 0
  fi
  echo "host_proxy_rollback=1"
  docker rm -f govpress-api govpress-worker >/dev/null 2>&1 || true
  if [ -n "${HOST_PROXY_API_BACKUP}" ] && docker inspect "${HOST_PROXY_API_BACKUP}" >/dev/null 2>&1; then
    docker rename "${HOST_PROXY_API_BACKUP}" govpress-api
    docker start govpress-api >/dev/null 2>&1 || true
  fi
  if [ -n "${HOST_PROXY_WORKER_BACKUP}" ] && docker inspect "${HOST_PROXY_WORKER_BACKUP}" >/dev/null 2>&1; then
    docker rename "${HOST_PROXY_WORKER_BACKUP}" govpress-worker
    docker start govpress-worker >/dev/null 2>&1 || true
  fi
  HOST_PROXY_BACKUP_ACTIVE=0
  HOST_PROXY_API_BACKUP=""
  HOST_PROXY_WORKER_BACKUP=""
}

host_proxy_cleanup_backups() {
  if [ "${HOST_PROXY_BACKUP_ACTIVE}" != "1" ]; then
    return 0
  fi
  if [ -n "${HOST_PROXY_API_BACKUP}" ] && docker inspect "${HOST_PROXY_API_BACKUP}" >/dev/null 2>&1; then
    docker rm -f "${HOST_PROXY_API_BACKUP}" >/dev/null 2>&1 || true
  fi
  if [ -n "${HOST_PROXY_WORKER_BACKUP}" ] && docker inspect "${HOST_PROXY_WORKER_BACKUP}" >/dev/null 2>&1; then
    docker rm -f "${HOST_PROXY_WORKER_BACKUP}" >/dev/null 2>&1 || true
  fi
  echo "host_proxy_backup_cleanup=1"
  HOST_PROXY_BACKUP_ACTIVE=0
  HOST_PROXY_API_BACKUP=""
  HOST_PROXY_WORKER_BACKUP=""
}

is_host_proxy_pid() {
  local pid="$1"
  sudo -n ps -p "$pid" -o args= 2>/dev/null | grep -q 'host_proxy.py'
}

cleanup_host_proxy_port_conflicts() {
  local ports="8080"
  local pids=""
  local port
  if ! sudo -n lsof -tiTCP:8080 -sTCP:LISTEN >/dev/null 2>&1 \
    && ! sudo -n ss -ltnp "( sport = :8080 )" >/dev/null 2>&1; then
    echo "host_proxy_port_conflict_cleanup=skipped_no_sudo"
    return 0
  fi
  for port in $ports; do
    pids="$pids $(
      {
        sudo -n lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true
        sudo -n ss -ltnp "( sport = :${port} )" 2>/dev/null \
          | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' || true
      } | sort -u
    )"
  done
  pids="$(printf '%s\n' "$pids" | tr ' ' '\n' | sed '/^$/d' | sort -u | tr '\n' ' ')"
  if [ -z "$pids" ]; then
    echo "host_proxy_port_conflict_cleanup=0"
    return
  fi
  echo "host_proxy_port_conflict_pids=$pids"
  for pid in $pids; do
    if is_host_proxy_pid "$pid"; then
      continue
    fi
    sudo -n kill "$pid" >/dev/null 2>&1 || true
  done
  sleep 1
  for port in $ports; do
    if ! wait_for_port_release "$port" 3 1 >/dev/null 2>&1; then
      local stubborn_pids=""
      stubborn_pids="$(
        {
          sudo -n lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true
          sudo -n ss -ltnp "( sport = :${port} )" 2>/dev/null \
            | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' || true
        } | sort -u | tr '\n' ' '
      )"
      for pid in $stubborn_pids; do
        if is_host_proxy_pid "$pid"; then
          continue
        fi
        sudo -n kill -9 "$pid" >/dev/null 2>&1 || true
      done
    fi
  done
  sleep 1
  echo "host_proxy_port_conflict_cleanup=1"
}

wait_for_port_release() {
  local port="$1"
  local attempts="${2:-20}"
  local delay="${3:-1}"
  local attempt
  for attempt in $(seq 1 "$attempts"); do
    if ! (sudo -n lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | grep -q .); then
      echo "port_${port}_released=1"
      return 0
    fi
    sleep "$delay"
  done
  echo "port_${port}_released=0"
  return 1
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
  sudo systemctl enable govpress-caddy.service
  sudo systemctl enable govpress-cloudflared.service
  sudo systemctl restart govpress-caddy.service || true
  local caddy_attempt
  for caddy_attempt in 1 2 3 4 5 6 7 8 9 10; do
    if systemctl is-active --quiet govpress-caddy.service; then
      break
    fi
    sleep 3
  done
  sudo systemctl status --no-pager govpress-caddy.service || true
  systemctl is-active --quiet govpress-caddy.service
  if systemctl is-active --quiet govpress-cloudflared.service; then
    echo "cloudflared_restart=skipped_active"
  else
    sudo systemctl restart govpress-cloudflared.service
  fi
  sudo systemctl status --no-pager govpress-caddy.service || true
  sudo systemctl status --no-pager govpress-cloudflared.service || true
  sudo journalctl -u govpress-caddy.service -n 30 --no-pager || true
  sudo journalctl -u govpress-cloudflared.service -n 30 --no-pager || true
}

restart_split_edge_tunnel() {
  require_passwordless_sudo
  sudo systemctl enable govpress-cloudflared.service
  if systemctl is-active --quiet govpress-cloudflared.service; then
    echo "cloudflared_restart=skipped_active"
  else
    sudo systemctl restart govpress-cloudflared.service
  fi
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

trap 'host_proxy_restore_backups; emit_compose_diagnostics' ERR

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
  ensure_converter_checkout
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
  normalize_env_placeholder_spec "$ENV_PATH"
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" "$CONVERTER_SPEC"
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "0"
  else
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" ""
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "1"
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
    restart_tunnel_after_compose=2
    if [ -z "${HEALTHCHECK_URL:-}" ] || [ "${HEALTHCHECK_URL}" = "http://127.0.0.1:8013/health" ]; then
      HEALTHCHECK_URL="http://127.0.0.1:8080/health"
      echo "healthcheck_url_override=$HEALTHCHECK_URL"
    fi
    echo "host_proxy_tunnel_origin=http://127.0.0.1:8080"
    echo "host_proxy_caddy_unit=govpress-caddy.service"
    echo "host_proxy_cloudflared_unit=govpress-cloudflared.service"
    run_host_proxy_compose_up
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
  build_and_verify_dashboard_assets compose "${GOVPRESS_QC_EXPORT_ROOT:-$DEPLOY_DIR/../gov-md-converter/exports/policy_briefing_qc}"
else
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  ENV_PATH="$DEPLOY_DIR/deploy/vps/.env"
  mkdir -p "$(dirname "$ENV_PATH")"
  touch "$ENV_PATH"
  normalize_env_placeholder_spec "$ENV_PATH"
  if [ -n "${CONVERTER_SPEC:-}" ]; then
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" "$CONVERTER_SPEC"
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "0"
  else
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_SPEC" ""
    upsert_env_value "$ENV_PATH" "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" "1"
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
  if [ -n "${CONVERTER_SPEC:-}" ] && [ "${CONVERTER_SPEC}" != "-" ]; then
    "$DEPLOY_DIR/.venv/bin/python" -m pip install "$CONVERTER_SPEC" -q
  fi
  if [ -n "${CONVERTER_SPEC:-}" ] && [ "${CONVERTER_SPEC}" != "-" ]; then
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
  build_and_verify_dashboard_assets baremetal "${GOVPRESS_QC_EXPORT_ROOT:-$DEPLOY_DIR/../gov-md-converter/exports/policy_briefing_qc}"
fi

# WSL rebuilds can take noticeably longer than VPS restarts.
health_code=""
policy_probe_code=""
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
  policy_probe_code="$(curl -sS -o /tmp/govpress-policy.txt -w '%{http_code}' "${policy_probe_header[@]}" 'http://127.0.0.1:8080/v1/policy-briefings/today?date=2026-04-08' || true)"
  echo "policy_probe_code=${policy_probe_code}"
  echo "policy_probe_body=$(head -c 200 /tmp/govpress-policy.txt | tr '\n' ' ' || true)"
  echo "deploy_probe_name=policy"
  echo "deploy_probe_code=${policy_probe_code}"
  test "${policy_probe_code}" = "200"
else
  echo "deploy_probe_name=health"
  echo "deploy_probe_code=${health_code}"
fi
if [ "${DEPLOY_MODE:-compose_proxy}" = "host_proxy" ]; then
  host_proxy_cleanup_backups
fi
echo "deploy-complete"
