#!/usr/bin/env bash
set -euo pipefail

CURRENT_USER="${SUDO_USER:-${USER:-$(id -un)}}"
SUDOERS_PATH="/etc/sudoers.d/govpress-read-shortener"

cat <<EOF | sudo tee "$SUDOERS_PATH" >/dev/null
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl daemon-reload
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl enable govpress-read-shortener.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart govpress-read-shortener.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status --no-pager govpress-read-shortener.service
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/journalctl -u govpress-read-shortener.service -n 50 --no-pager
${CURRENT_USER} ALL=(root) NOPASSWD: /usr/bin/tee /etc/systemd/system/govpress-read-shortener.service
EOF

sudo chmod 440 "$SUDOERS_PATH"
sudo visudo -cf "$SUDOERS_PATH"
echo "installed $SUDOERS_PATH for ${CURRENT_USER}"
