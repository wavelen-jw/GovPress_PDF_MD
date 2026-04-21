#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DEPLOY_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_SH="$DEPLOY_DIR/bin/compose.sh"

export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"
unset DOCKER_CONTEXT

if [ ! -x "$COMPOSE_SH" ]; then
  echo "watchdog_reconcile=error reason=compose_missing path=$COMPOSE_SH" >&2
  exit 127
fi

container_running() {
  local name="$1"
  local state=""
  state="$(docker inspect --format '{{.State.Status}}' "$name" 2>/dev/null || true)"
  [ "$state" = "running" ]
}

container_healthy_or_unknown() {
  local name="$1"
  local health=""
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || true)"
  [ "$health" = "healthy" ] || [ "$health" = "none" ]
}

need_reconcile=0
reasons=()

for name in govpress-api govpress-worker; do
  if ! container_running "$name"; then
    need_reconcile=1
    reasons+=("${name}:not_running")
    continue
  fi
  if ! container_healthy_or_unknown "$name"; then
    need_reconcile=1
    reasons+=("${name}:unhealthy")
  fi
done

if [ "$need_reconcile" -eq 0 ]; then
  echo "watchdog_reconcile=skip reason=containers_healthy"
  exit 0
fi

echo "watchdog_reconcile=run reasons=${reasons[*]}"
"$COMPOSE_SH" up -d api worker

for i in $(seq 1 20); do
  if curl -sf http://127.0.0.1:8013/health >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

if systemctl is-enabled govpress-caddy.service >/dev/null 2>&1; then
  systemctl restart govpress-caddy.service || true
fi

if systemctl is-enabled govpress-cloudflared.service >/dev/null 2>&1; then
  if ! systemctl is-active --quiet govpress-cloudflared.service; then
    systemctl restart govpress-cloudflared.service || true
  fi
fi

curl -sf http://127.0.0.1:8013/health >/dev/null
echo "watchdog_reconcile=ok"
