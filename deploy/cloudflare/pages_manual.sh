#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)

COMMAND="${1:-status}"
if [ "$#" -gt 0 ]; then
  shift
fi

SOURCE_ROOT="${GOVPRESS_PAGES_SOURCE_ROOT:-$REPOSITORY_ROOT}"
STATE_ROOT="${GOVPRESS_PAGES_STATE_ROOT:-/home/wavel/.govpress-pages}"
PROJECT="${GOVPRESS_PAGES_PROJECT:-readhim-web}"
PRODUCTION_BRANCH="${GOVPRESS_PAGES_PRODUCTION_BRANCH:-web}"
REF="${1:-${GOVPRESS_PAGES_REF:-web}}"
WRANGLER_VERSION="${GOVPRESS_WRANGLER_VERSION:-4}"
LIVE_ENV="${GOVPRESS_PAGES_LIVE_ENV:-/home/wavel/GovPress_PDF_MD/deploy/wsl/.env}"

die() {
  echo "pages_manual: $*" >&2
  exit 1
}

case "$STATE_ROOT" in
  ""|/|/home|/home/wavel) die "GOVPRESS_PAGES_STATE_ROOT is too broad: $STATE_ROOT" ;;
esac

mkdir -p "$STATE_ROOT/locks" "$STATE_ROOT/releases" "$STATE_ROOT/npm-cache" "$STATE_ROOT/tmp"
exec 9>"$STATE_ROOT/locks/pages.lock"
flock -n 9 || die "another Pages operation is already running"

TEMP_BUILD_ROOT=""
cleanup() {
  case "$TEMP_BUILD_ROOT" in
    "$STATE_ROOT/tmp/build."*) rm -rf -- "$TEMP_BUILD_ROOT" ;;
  esac
}
trap cleanup EXIT

source_sha() {
  git -C "$SOURCE_ROOT" rev-parse HEAD
}

read_api_key() {
  if [ -n "${EXPO_PUBLIC_GOVPRESS_API_KEY:-}" ]; then
    return
  fi
  if [ -f "$LIVE_ENV" ]; then
    EXPO_PUBLIC_GOVPRESS_API_KEY=$(python3 - "$LIVE_ENV" <<'PY'
from pathlib import Path
import sys

for raw_line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if line.startswith("GOVPRESS_API_KEY="):
        print(line.split("=", 1)[1].strip().strip('"').strip("'"))
        break
PY
)
    export EXPO_PUBLIC_GOVPRESS_API_KEY
  fi
}

wrangler() {
  npx --yes "wrangler@$WRANGLER_VERSION" "$@"
}

require_auth() {
  [ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] || die "CLOUDFLARE_ACCOUNT_ID is required"
  if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
    wrangler whoami >/dev/null || die "Wrangler login or CLOUDFLARE_API_TOKEN is required"
  fi
}

build_release() {
  [ -f "$SOURCE_ROOT/mobile/package-lock.json" ] || die "invalid source root: $SOURCE_ROOT"
  local sha release temporary
  sha=$(source_sha)
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "source is not an exact Git commit"
  release="$STATE_ROOT/releases/$sha"
  if [ -f "$release/source.sha" ] && [ "$(tr -d '[:space:]' < "$release/source.sha")" = "$sha" ]; then
    echo "$release"
    return
  fi
  [ ! -e "$release" ] || die "incomplete release already exists: $release"

  TEMP_BUILD_ROOT=$(mktemp -d "$STATE_ROOT/tmp/build.XXXXXX")
  git -C "$SOURCE_ROOT" archive "$sha" | tar -x -C "$TEMP_BUILD_ROOT"
  read_api_key
  (
    cd "$TEMP_BUILD_ROOT/mobile"
    npm ci --cache "$STATE_ROOT/npm-cache"
    npm run export:web
  ) >&2
  temporary="$STATE_ROOT/releases/.${sha}.$$"
  [ ! -e "$temporary" ] || die "temporary release already exists: $temporary"
  python3 "$SCRIPT_DIR/assemble_pages_artifact.py" \
    --source "$TEMP_BUILD_ROOT" \
    --destination "$temporary" >&2
  printf '%s\n' "$sha" > "$temporary/source.sha"
  printf '%s\n' "$REF" > "$temporary/source.ref"
  printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$temporary/built-at"
  mv -- "$temporary" "$release"
  rm -rf -- "$TEMP_BUILD_ROOT"
  TEMP_BUILD_ROOT=""
  echo "$release"
}

show_status() {
  echo "project=$PROJECT"
  echo "production_branch=$PRODUCTION_BRANCH"
  echo "source_root=$SOURCE_ROOT"
  echo "source_sha=$(source_sha 2>/dev/null || echo unavailable)"
  echo "account_id_present=$([ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] && echo yes || echo no)"
  echo "api_token_present=$([ -n "${CLOUDFLARE_API_TOKEN:-}" ] && echo yes || echo no)"
  echo "deployment_mode=manual_only"
}

case "$COMMAND" in
  status)
    show_status
    ;;
  auth)
    require_auth
    wrangler whoami
    ;;
  build)
    build_release
    ;;
  create-project)
    require_auth
    [ "${GOVPRESS_PAGES_CONFIRM_PROJECT:-}" = "$PROJECT" ] \
      || die "set GOVPRESS_PAGES_CONFIRM_PROJECT=$PROJECT to create the project"
    wrangler pages project create "$PROJECT" --production-branch "$PRODUCTION_BRANCH"
    ;;
  preview)
    require_auth
    release=$(build_release)
    sha=$(tr -d '[:space:]' < "$release/source.sha")
    branch="preview-${sha:0:12}"
    wrangler pages deploy "$release" \
      --project-name "$PROJECT" \
      --branch "$branch" \
      --commit-hash "$sha" \
      --commit-message "Manual preview $sha"
    ;;
  production)
    require_auth
    release=$(build_release)
    sha=$(tr -d '[:space:]' < "$release/source.sha")
    [ "${GOVPRESS_PAGES_CONFIRM_SHA:-}" = "$sha" ] \
      || die "set GOVPRESS_PAGES_CONFIRM_SHA=$sha to deploy production"
    wrangler pages deploy "$release" \
      --project-name "$PROJECT" \
      --branch "$PRODUCTION_BRANCH" \
      --commit-hash "$sha" \
      --commit-message "Manual production $sha"
    ;;
  *)
    die "usage: $0 [status|auth|build|create-project|preview|production]"
    ;;
esac
