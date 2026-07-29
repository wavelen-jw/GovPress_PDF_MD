#!/usr/bin/env bash
set -Eeuo pipefail

CONTAINER="${1:-${MCP_CONTAINER:-govpress-mcp-server-1}}"
EXPECTED_VERSION="${GOVPRESS_HWPX_MD_EXPECTED_VERSION:-0.4.7}"
EXPECTED_COMMIT="${GOVPRESS_HWPX_MD_EXPECTED_COMMIT:-c2960871aa22e3d369dc10f05558767d8f272259}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" | grep -qx true
IMAGE_ID="$(docker inspect -f '{{.Image}}' "$CONTAINER")"
IMAGE_VERSION="$(docker image inspect -f '{{index .Config.Labels "org.opencontainers.image.version"}}' "$IMAGE_ID")"
IMAGE_COMMIT="$(docker image inspect -f '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$IMAGE_ID")"
WHEEL_SHA256="$(docker image inspect -f '{{index .Config.Labels "cloud.govpress.converter.wheel-sha256"}}' "$IMAGE_ID")"

[[ "$IMAGE_VERSION" == "$EXPECTED_VERSION" ]] || {
  echo "converter preflight failed: image version=$IMAGE_VERSION expected=$EXPECTED_VERSION" >&2
  exit 1
}
[[ "$IMAGE_COMMIT" == "$EXPECTED_COMMIT" ]] || {
  echo "converter preflight failed: image commit=$IMAGE_COMMIT expected=$EXPECTED_COMMIT" >&2
  exit 1
}
[[ "$WHEEL_SHA256" =~ ^[0-9a-f]{64}$ ]] || {
  echo "converter preflight failed: invalid wheel SHA-256 label" >&2
  exit 1
}

docker exec \
  -e "GOVPRESS_HWPX_MD_EXPECTED_VERSION=$EXPECTED_VERSION" \
  "$CONTAINER" \
  /opt/govpress-hwpx-md-venv/bin/python \
  /usr/local/libexec/govpress-converter-preflight.py \
  --check-only

printf 'container=%s\nimage_id=%s\nversion=%s\ncommit=%s\nwheel_sha256=%s\n' \
  "$CONTAINER" "$IMAGE_ID" "$IMAGE_VERSION" "$IMAGE_COMMIT" "$WHEEL_SHA256"
