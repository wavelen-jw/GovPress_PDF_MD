#!/usr/bin/env bash
set -euo pipefail

CURRENT_USER="${SUDO_USER:-${USER:-$(id -un)}}"
SUDOERS_PATH="/etc/sudoers.d/govpress-remote-deploy"

cat <<EOF | sudo tee "$SUDOERS_PATH" >/dev/null
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl daemon-reload
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl enable govpress-compose.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl enable govpress-caddy.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl enable govpress-cloudflared.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl enable govpress-watchdog.timer
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart govpress-compose.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart govpress-caddy.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart govpress-cloudflared.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart govpress-watchdog.timer
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-compose.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-caddy.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-cloudflared.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-watchdog.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-watchdog.timer
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/journalctl -u govpress-caddy.service -n 30 --no-pager
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/journalctl -u govpress-cloudflared.service -n 30 --no-pager
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/journalctl -u govpress-watchdog.service -n 30 --no-pager
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-compose.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-caddy.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-cloudflared.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-watchdog.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-watchdog.timer
EOF

sudo chmod 440 "$SUDOERS_PATH"
sudo visudo -cf "$SUDOERS_PATH"
echo "installed $SUDOERS_PATH for ${CURRENT_USER}"
