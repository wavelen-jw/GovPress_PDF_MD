#!/usr/bin/env bash
set -euo pipefail

sed -E \
  -e 's/(--token[= ]+)[^[:space:]]+/\1[REDACTED]/g' \
  -e 's/(--service-token-secret[= ]+)[^[:space:]]+/\1[REDACTED]/g' \
  -e 's/(CLOUDFLARE_TUNNEL_TOKEN=)[^[:space:]]+/\1[REDACTED]/g' \
  -e 's#(https://)[^/@[:space:]]+@github\.com#\1[REDACTED]@github.com#g'
