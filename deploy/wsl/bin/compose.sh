#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DEPLOY_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="${COMPOSE_FILE_OVERRIDE:-$DEPLOY_DIR/docker-compose.yml}"
HOST_PROXY_COMPOSE_FILE="$DEPLOY_DIR/docker-compose.host-proxy.yml"
ENV_FILE="$DEPLOY_DIR/.env"

# Docker Desktop contexts can drift to the Windows npipe endpoint inside WSL.
# Force the local Linux daemon socket unless the caller explicitly overrides it.
export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"
unset DOCKER_CONTEXT
export COMPOSE_DOCKER_CLI_BUILD="${COMPOSE_DOCKER_CLI_BUILD:-0}"
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"

HOME_DIR="${HOME:-$(getent passwd $(id -u) | cut -d: -f6)}"
DOCKER_CONFIG_DIR="${DOCKER_CONFIG:-$HOME_DIR/.docker}"
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/config.json"
if [[ -f "$DOCKER_CONFIG_FILE" ]] \
  && grep -q '"credsStore"' "$DOCKER_CONFIG_FILE" \
  && grep -q '"desktop.exe"' "$DOCKER_CONFIG_FILE" \
  && ! command -v docker-credential-desktop.exe >/dev/null 2>&1; then
  export DOCKER_CONFIG="$HOME_DIR/.cache/govpress-docker-config"
  mkdir -p "$DOCKER_CONFIG"
  cat > "$DOCKER_CONFIG/config.json" <<'EOF'
{
  "auths": {}
}
EOF
fi

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <docker-compose args...>" >&2
  exit 1
fi

DEPLOY_MODE="${GOVPRESS_DEPLOY_MODE:-}"
if [[ -z "$DEPLOY_MODE" ]] && [[ -f "$ENV_FILE" ]]; then
  DEPLOY_MODE=$(grep -E '^GOVPRESS_DEPLOY_MODE=' "$ENV_FILE" | tail -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs || true)
fi

CONVERTER_VERSION_FILE="$DEPLOY_DIR/../converter.version"
CONVERTER_SPEC_RESOLVER="$DEPLOY_DIR/../common/resolve_converter_spec.py"

normalize_env_converter_spec() {
  [[ -f "$ENV_FILE" ]] || return 0
  [[ -f "$CONVERTER_VERSION_FILE" ]] || return 0
  [[ -f "$CONVERTER_SPEC_RESOLVER" ]] || return 0
  python3 - <<'PY' "$ENV_FILE" "$CONVERTER_VERSION_FILE" "$CONVERTER_SPEC_RESOLVER"
from pathlib import Path
import subprocess
import sys

env_path = Path(sys.argv[1])
version_file = Path(sys.argv[2])
resolver = Path(sys.argv[3])
lines = env_path.read_text(encoding="utf-8").splitlines()
updated: list[str] = []
changed = False
for line in lines:
    if line.startswith("GOVPRESS_CONVERTER_SPEC="):
        spec = line.split("=", 1)[1]
        if spec.strip() == "-":
            normalized = ""
        else:
            normalized = subprocess.check_output(
                [sys.executable, str(resolver), "--spec", spec, "--version-file", str(version_file)],
                text=True,
            ).strip()
        updated.append(f"GOVPRESS_CONVERTER_SPEC={normalized}")
        changed = changed or normalized != spec
    else:
        updated.append(line)
if changed:
    env_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
PY
}

normalize_env_converter_spec

if [[ -z "${COMPOSE_FILE_OVERRIDE:-}" ]] && [[ "$DEPLOY_MODE" == "host_proxy" ]] && [[ -f "$HOST_PROXY_COMPOSE_FILE" ]]; then
  COMPOSE_FILE="$HOST_PROXY_COMPOSE_FILE"
fi

cleanup_host_proxy_runtime_conflicts() {
  if [[ "$DEPLOY_MODE" != "host_proxy" ]]; then
    return 0
  fi
  case "${1:-}" in
    up|start|restart)
      docker rm -f govpress-caddy-host govpress-caddy govpress-cloudflared >/dev/null 2>&1 || true
      if sudo -n true >/dev/null 2>&1; then
        local pids=""
        local pid=""
        pids="$(
          {
            sudo lsof -tiTCP:8080 -sTCP:LISTEN 2>/dev/null || true
            sudo ss -ltnp '( sport = :8080 )' 2>/dev/null \
              | sed -n 's/.*pid=\([0-9]\+\).*/\1/p'
          } | sort -u
        )"
        if [[ -n "$pids" ]]; then
          while IFS= read -r pid; do
            [[ -n "$pid" ]] || continue
            if sudo -n ps -p "$pid" -o args= 2>/dev/null | grep -q 'host_proxy.py'; then
              continue
            fi
            sudo kill "$pid" >/dev/null 2>&1 || true
          done <<< "$pids"
          sleep 1
          while IFS= read -r pid; do
            [[ -n "$pid" ]] || continue
            if sudo -n ps -p "$pid" -o args= 2>/dev/null | grep -q 'host_proxy.py'; then
              continue
            fi
            sudo kill -9 "$pid" >/dev/null 2>&1 || true
          done <<< "$pids"
        fi
      fi
      ;;
  esac
}

cleanup_host_proxy_runtime_conflicts "${1:-}"

if [[ -x "$HOME_DIR/.local/bin/docker-compose" ]]; then
  exec "$HOME_DIR/.local/bin/docker-compose" -f "$COMPOSE_FILE" "$@"
fi

if docker compose version >/dev/null 2>&1; then
  exec docker compose -f "$COMPOSE_FILE" "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose -f "$COMPOSE_FILE" "$@"
fi

echo "docker compose is not available" >&2
exit 1
