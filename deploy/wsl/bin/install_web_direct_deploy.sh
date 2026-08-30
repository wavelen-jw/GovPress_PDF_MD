#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
STATE_ROOT="${GOVPRESS_WEB_STATE_ROOT:-/home/wavel/.govpress-web}"
SERVE_ROOT="${GOVPRESS_WEB_SERVE_ROOT:-/home/wavel/GovPress_PDF_MD}"
INTERVAL="${GOVPRESS_WEB_CRON_INTERVAL:-*/5 * * * *}"
INSTALL_CRON=0
DEPLOY_NOW=0

for argument in "$@"; do
  case "$argument" in
    --no-cron) INSTALL_CRON=0 ;;
    --deploy-now) DEPLOY_NOW=1 ;;
    *) echo "usage: $0 [--no-cron] [--deploy-now]" >&2; exit 2 ;;
  esac
done

case "$STATE_ROOT" in
  ""|/|/home|/home/wavel) echo "unsafe GOVPRESS_WEB_STATE_ROOT: $STATE_ROOT" >&2; exit 1 ;;
esac
case "$SERVE_ROOT" in
  ""|/|/home|/home/wavel) echo "unsafe GOVPRESS_WEB_SERVE_ROOT: $SERVE_ROOT" >&2; exit 1 ;;
esac

DEPLOY_SOURCE="$SCRIPT_DIR/deploy_web_direct.sh"
HELPER_SOURCE="$REPOSITORY_ROOT/deploy/common/materialize-web-source.py"
[ -x "$DEPLOY_SOURCE" ] || { echo "missing deployer: $DEPLOY_SOURCE" >&2; exit 1; }
[ -x "$HELPER_SOURCE" ] || { echo "missing materializer: $HELPER_SOURCE" >&2; exit 1; }
[ -d "$SERVE_ROOT/ui" ] || { echo "missing live UI directory: $SERVE_ROOT/ui" >&2; exit 1; }
[ -d "$SERVE_ROOT/mobile/dist" ] || { echo "missing live app directory: $SERVE_ROOT/mobile/dist" >&2; exit 1; }

INSTALL_ROOT="$STATE_ROOT/bin"
mkdir -p "$INSTALL_ROOT" "$STATE_ROOT/logs"
install -m 0755 "$DEPLOY_SOURCE" "$INSTALL_ROOT/deploy_web_direct.sh"
install -m 0755 "$HELPER_SOURCE" "$INSTALL_ROOT/materialize-web-source.py"

if [ "$INSTALL_CRON" = "1" ]; then
  CRON_MARKER="# govpress-serverw-web-direct-deploy"
  CRON_TEMP=$(mktemp)
  trap 'rm -f -- "$CRON_TEMP"' EXIT
  crontab -l 2>/dev/null | grep -vF "$CRON_MARKER" > "$CRON_TEMP" || true
  printf '%s\n' "$CRON_MARKER" >> "$CRON_TEMP"
  printf '%s PATH=/usr/local/bin:/usr/bin:/bin GOVPRESS_WEB_SERVE_ROOT=%q GOVPRESS_WEB_STATE_ROOT=%q GOVPRESS_WEB_HELPER=%q GOVPRESS_WEB_PUBLIC_CURL_INSECURE=1 %q deploy web >> %q 2>&1 %s\n' \
    "$INTERVAL" \
    "$SERVE_ROOT" \
    "$STATE_ROOT" \
    "$INSTALL_ROOT/materialize-web-source.py" \
    "$INSTALL_ROOT/deploy_web_direct.sh" \
    "$STATE_ROOT/logs/deploy.log" \
    "$CRON_MARKER" \
    >> "$CRON_TEMP"
  crontab "$CRON_TEMP"
fi

echo "install_status=success"
echo "deployer=$INSTALL_ROOT/deploy_web_direct.sh"
echo "state_root=$STATE_ROOT"
echo "serve_root=$SERVE_ROOT"
echo "cron_installed=$INSTALL_CRON"
if command -v systemctl >/dev/null 2>&1; then
  echo "cron_service=$(systemctl is-active cron 2>/dev/null || echo unknown)"
fi

if [ "$DEPLOY_NOW" = "1" ]; then
  GOVPRESS_WEB_SERVE_ROOT="$SERVE_ROOT" \
  GOVPRESS_WEB_STATE_ROOT="$STATE_ROOT" \
  GOVPRESS_WEB_HELPER="$INSTALL_ROOT/materialize-web-source.py" \
  GOVPRESS_WEB_PUBLIC_CURL_INSECURE=1 \
    "$INSTALL_ROOT/deploy_web_direct.sh" deploy web
fi
