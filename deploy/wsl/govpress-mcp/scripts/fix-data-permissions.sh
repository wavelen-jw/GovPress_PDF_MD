#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uid="$(id -u)"
gid="$(id -g)"

docker run --rm \
  -v "$PWD/data:/data" \
  --entrypoint sh \
  govpress-mcp-converter:latest \
  -lc "chown -R $uid:$gid /data"
