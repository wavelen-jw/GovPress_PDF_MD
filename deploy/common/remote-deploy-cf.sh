#!/usr/bin/env bash
set -euo pipefail

echo "=== govpress remote diagnostics ==="
echo "remote_host=$(hostname)"
echo "remote_user=$(whoami)"
echo "deploy_dir=${DEPLOY_DIR}"
echo "target_branch=${BRANCH}"

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

# Keep deploy-time cache eviction explicit so policy briefing fixes go live on
# every server even when only cached converted output would differ.
rm -f \
  "$DEPLOY_DIR/deploy/wsl/data/storage/policy_briefing_cache/index.json" \
  "$DEPLOY_DIR"/deploy/wsl/data/storage/policy_briefing_catalog/*.json \
  "$DEPLOY_DIR/storage/policy_briefing_cache/index.json" \
  "$DEPLOY_DIR"/storage/policy_briefing_catalog/*.json \
  2>/dev/null || true
echo "policy_cache_reset=1"

if [ -n "${COMPOSE_FILE:-}" ]; then
  COMPOSE_PATH="$DEPLOY_DIR/$COMPOSE_FILE"
  ENV_PATH="$(dirname "$COMPOSE_PATH")/.env"
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
  if [ -x "$DEPLOY_DIR/deploy/wsl/bin/compose.sh" ]; then
    "$DEPLOY_DIR/deploy/wsl/bin/compose.sh" up -d --build
    "$DEPLOY_DIR/deploy/wsl/bin/compose.sh" ps
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_PATH" up -d --build
    docker-compose -f "$COMPOSE_PATH" ps
  else
    docker compose -f "$COMPOSE_PATH" up -d --build
    docker compose -f "$COMPOSE_PATH" ps
  fi
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
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  health_code="$(curl -sS -o /tmp/govpress-health.txt -w '%{http_code}' "$HEALTHCHECK_URL" || true)"
  if [ "$health_code" = "200" ]; then
    break
  fi
  sleep 3
done
echo "health_probe_code=$health_code"
test "$health_code" = "200"
echo "policy_probe_code=$(curl -sS -o /tmp/govpress-policy.txt -w '%{http_code}' 'http://127.0.0.1:8080/v1/policy-briefings/today?date=2026-04-08' || true)"
echo "policy_probe_body=$(head -c 200 /tmp/govpress-policy.txt | tr '\n' ' ' || true)"
echo "deploy-complete"
