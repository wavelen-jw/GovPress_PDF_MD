#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DEPLOY_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"

# Docker Desktop contexts can drift to the Windows npipe endpoint inside WSL.
# Force the local Linux daemon socket unless the caller explicitly overrides it.
export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"
unset DOCKER_CONTEXT
export COMPOSE_DOCKER_CLI_BUILD="${COMPOSE_DOCKER_CLI_BUILD:-0}"
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"

DOCKER_CONFIG_DIR="${DOCKER_CONFIG:-$HOME/.docker}"
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/config.json"
if [[ -f "$DOCKER_CONFIG_FILE" ]] \
  && grep -q '"credsStore"' "$DOCKER_CONFIG_FILE" \
  && grep -q '"desktop.exe"' "$DOCKER_CONFIG_FILE" \
  && ! command -v docker-credential-desktop.exe >/dev/null 2>&1; then
  export DOCKER_CONFIG="$HOME/.cache/govpress-docker-config"
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

if [[ -x "$HOME/.local/bin/docker-compose" ]]; then
  exec "$HOME/.local/bin/docker-compose" -f "$COMPOSE_FILE" "$@"
fi

if docker compose version >/dev/null 2>&1; then
  exec docker compose -f "$COMPOSE_FILE" "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose -f "$COMPOSE_FILE" "$@"
fi

echo "docker compose is not available" >&2
exit 1
