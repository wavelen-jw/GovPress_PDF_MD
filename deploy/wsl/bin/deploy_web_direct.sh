#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(cd -- "$SCRIPT_DIR/../../.." 2>/dev/null && pwd || true)

COMMAND="${1:-deploy}"
if [ "$COMMAND" = "deploy" ] && [ "$#" -gt 0 ]; then
  shift
fi

SERVE_ROOT="${GOVPRESS_WEB_SERVE_ROOT:-/home/wavel/GovPress_PDF_MD}"
STATE_ROOT="${GOVPRESS_WEB_STATE_ROOT:-/home/wavel/.govpress-web}"
REPOSITORY="${GOVPRESS_WEB_REPOSITORY:-wavelen-jw/GovPress_PDF_MD}"
GIT_URL="${GOVPRESS_WEB_GIT_URL:-git@github.com:wavelen-jw/GovPress_PDF_MD.git}"
SOURCE_MODE="${GOVPRESS_WEB_SOURCE_MODE:-git}"
REF="${1:-${GOVPRESS_WEB_REF:-web}}"
SOURCE_DIR="${GOVPRESS_WEB_SOURCE_DIR:-}"
EXPECTED_SHA="${GOVPRESS_WEB_EXPECT_SHA:-}"
LOCAL_URL="${GOVPRESS_WEB_LOCAL_URL-http://127.0.0.1:8080}"
PUBLIC_URL="${GOVPRESS_WEB_PUBLIC_URL-https://govpress.cloud}"
KEEP_BACKUPS="${GOVPRESS_WEB_KEEP_BACKUPS:-10}"
RUN_TYPECHECK="${GOVPRESS_WEB_RUN_TYPECHECK:-0}"
SKIP_BUILD="${GOVPRESS_WEB_SKIP_BUILD:-0}"
ALLOW_DIRTY_STATIC="${GOVPRESS_WEB_ALLOW_DIRTY_STATIC:-0}"
PUBLIC_CURL_INSECURE="${GOVPRESS_WEB_PUBLIC_CURL_INSECURE:-0}"

if [ -x "$SCRIPT_DIR/materialize-web-source.py" ]; then
  HELPER="${GOVPRESS_WEB_HELPER:-$SCRIPT_DIR/materialize-web-source.py}"
else
  HELPER="${GOVPRESS_WEB_HELPER:-$REPOSITORY_ROOT/deploy/common/materialize-web-source.py}"
fi

die() {
  echo "deploy_web_direct: $*" >&2
  exit 1
}

validate_root() {
  local label="$1"
  local path="$2"
  case "$path" in
    ""|/|/home|/home/wavel)
      die "$label is too broad: $path"
      ;;
  esac
}

validate_root "GOVPRESS_WEB_SERVE_ROOT" "$SERVE_ROOT"
validate_root "GOVPRESS_WEB_STATE_ROOT" "$STATE_ROOT"
[[ "$KEEP_BACKUPS" =~ ^[1-9][0-9]*$ ]] || die "GOVPRESS_WEB_KEEP_BACKUPS must be a positive integer"

mkdir -p "$STATE_ROOT/locks" "$STATE_ROOT/releases" "$STATE_ROOT/backups" "$STATE_ROOT/tmp"
exec 9>"$STATE_ROOT/locks/deploy.lock"
flock -n 9 || die "another web deployment is already running"

CURRENT_SHA_PATH="$STATE_ROOT/current.sha"
CURRENT_REF_PATH="$STATE_ROOT/current.ref"

current_sha() {
  if [ -f "$CURRENT_SHA_PATH" ]; then
    tr -d '[:space:]' < "$CURRENT_SHA_PATH"
  elif git -C "$SERVE_ROOT" rev-parse HEAD >/dev/null 2>&1; then
    git -C "$SERVE_ROOT" rev-parse HEAD
  else
    echo unmanaged
  fi
}

write_marker() {
  local path="$1"
  local value="$2"
  local temporary="$path.tmp.$$"
  printf '%s\n' "$value" > "$temporary"
  mv -f -- "$temporary" "$path"
}

asset_tree_is_valid() {
  local root="$1"
  [ -f "$root/ui/landing.html" ] \
    && [ -f "$root/mobile/dist/index.html" ] \
    && [ -d "$root/mobile/dist/_expo" ]
}

curl_to_file() {
  local url="$1"
  local output="$2"
  local -a options=(--fail --silent --show-error --location --max-time 20)
  if [ "$PUBLIC_CURL_INSECURE" = "1" ] && [[ "$url" == https://* ]]; then
    options+=(--insecure)
  fi
  curl "${options[@]}" "$url" -o "$output"
}

probe_assets() (
  local asset_root="$1"
  local source_sha="$2"
  local expected_landing expected_app probe_file actual
  expected_landing=$(sha256sum "$asset_root/ui/landing.html" | awk '{print $1}')
  expected_app=$(sha256sum "$asset_root/mobile/dist/index.html" | awk '{print $1}')
  probe_file=$(mktemp "$STATE_ROOT/tmp/probe.XXXXXX")
  trap 'rm -f -- "$probe_file"' EXIT

  if [ -n "$LOCAL_URL" ]; then
    curl_to_file "${LOCAL_URL%/}/?deploy=$source_sha" "$probe_file"
    actual=$(sha256sum "$probe_file" | awk '{print $1}')
    [ "$actual" = "$expected_landing" ] || return 1
    curl_to_file "${LOCAL_URL%/}/app/?deploy=$source_sha" "$probe_file"
    actual=$(sha256sum "$probe_file" | awk '{print $1}')
    [ "$actual" = "$expected_app" ] || return 1
  fi

  if [ -n "$PUBLIC_URL" ]; then
    local matched=0
    for _ in 1 2 3 4 5 6; do
      if curl_to_file "${PUBLIC_URL%/}/?deploy=$source_sha" "$probe_file"; then
        actual=$(sha256sum "$probe_file" | awk '{print $1}')
        if [ "$actual" = "$expected_landing" ]; then
          matched=1
          break
        fi
      fi
      sleep 5
    done
    [ "$matched" = "1" ] || return 1
  fi
)

cleanup_old_backups() {
  local -a backups=()
  mapfile -t backups < <(
    find "$STATE_ROOT/backups" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' \
      | sort -rn \
      | cut -d' ' -f2-
  )
  local index candidate
  for ((index=KEEP_BACKUPS; index<${#backups[@]}; index++)); do
    candidate="${backups[$index]}"
    case "$candidate" in
      "$STATE_ROOT/backups/"*) rm -rf -- "$candidate" ;;
      *) die "refusing to prune unexpected backup path: $candidate" ;;
    esac
  done
}

activate_assets() {
  local asset_root="$1"
  local source_sha="$2"
  local source_ref="$3"
  asset_tree_is_valid "$asset_root" || die "release asset tree is incomplete: $asset_root"
  [ -d "$SERVE_ROOT/ui" ] || die "live UI directory is missing: $SERVE_ROOT/ui"
  [ -d "$SERVE_ROOT/mobile/dist" ] || die "live app directory is missing: $SERVE_ROOT/mobile/dist"

  local ui_stage="$SERVE_ROOT/.ui.direct-deploy.$$"
  local app_stage="$SERVE_ROOT/mobile/.dist.direct-deploy.$$"
  local backup_id backup_root old_sha
  backup_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  backup_root="$STATE_ROOT/backups/$backup_id"
  old_sha=$(current_sha)

  mkdir -p "$ui_stage" "$app_stage" "$backup_root/mobile"
  rsync -a --delete "$asset_root/ui/" "$ui_stage/"
  rsync -a --delete "$asset_root/mobile/dist/" "$app_stage/"
  [ -f "$ui_stage/landing.html" ] || die "staged landing page is missing"
  [ -f "$app_stage/index.html" ] || die "staged app index is missing"
  [ -d "$app_stage/_expo" ] || die "staged app bundle is missing"

  printf '%s\n' "$old_sha" > "$backup_root/source.sha"
  printf '%s\n' "${source_ref:-unknown}" > "$backup_root/replaced-by.ref"

  local ui_swapped=0 app_swapped=0
  if ! mv -- "$SERVE_ROOT/ui" "$backup_root/ui"; then
    die "could not back up the live UI directory"
  fi
  ui_swapped=1
  if ! mv -- "$ui_stage" "$SERVE_ROOT/ui"; then
    mv -- "$backup_root/ui" "$SERVE_ROOT/ui"
    die "could not activate the staged UI directory"
  fi
  if ! mv -- "$SERVE_ROOT/mobile/dist" "$backup_root/mobile/dist"; then
    mv -- "$SERVE_ROOT/ui" "$ui_stage"
    mv -- "$backup_root/ui" "$SERVE_ROOT/ui"
    die "could not back up the live app directory"
  fi
  app_swapped=1
  if ! mv -- "$app_stage" "$SERVE_ROOT/mobile/dist"; then
    mv -- "$backup_root/mobile/dist" "$SERVE_ROOT/mobile/dist"
    mv -- "$SERVE_ROOT/ui" "$ui_stage"
    mv -- "$backup_root/ui" "$SERVE_ROOT/ui"
    die "could not activate the staged app directory"
  fi

  if ! probe_assets "$asset_root" "$source_sha"; then
    echo "smoke_result=failed rollback=starting" >&2
    if [ "$app_swapped" = "1" ]; then
      mv -- "$SERVE_ROOT/mobile/dist" "$app_stage"
      mv -- "$backup_root/mobile/dist" "$SERVE_ROOT/mobile/dist"
    fi
    if [ "$ui_swapped" = "1" ]; then
      mv -- "$SERVE_ROOT/ui" "$ui_stage"
      mv -- "$backup_root/ui" "$SERVE_ROOT/ui"
    fi
    rm -rf -- "$ui_stage" "$app_stage" "$backup_root"
    die "static smoke test failed; previous release restored"
  fi

  write_marker "$CURRENT_SHA_PATH" "$source_sha"
  write_marker "$CURRENT_REF_PATH" "$source_ref"
  printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_ROOT/last-success-at"
  cleanup_old_backups
  echo "deploy_status=success"
  echo "source_sha=$source_sha"
  echo "source_ref=$source_ref"
  echo "backup=$backup_root"
}

show_status() {
  echo "current_sha=$(current_sha)"
  echo "current_ref=$(cat "$CURRENT_REF_PATH" 2>/dev/null || echo unknown)"
  echo "last_success_at=$(cat "$STATE_ROOT/last-success-at" 2>/dev/null || echo never)"
  if [ -n "$LOCAL_URL" ]; then
    echo "local_root_http=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${LOCAL_URL%/}/" || true)"
    echo "local_app_http=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${LOCAL_URL%/}/app/" || true)"
  fi
}

rollback_latest() {
  local backup
  backup=$(
    find "$STATE_ROOT/backups" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' \
      | sort -rn \
      | head -1 \
      | cut -d' ' -f2-
  )
  [ -n "$backup" ] || die "no direct-deploy backup is available"
  asset_tree_is_valid "$backup" || die "latest backup is incomplete: $backup"
  local rollback_sha
  rollback_sha=$(tr -d '[:space:]' < "$backup/source.sha")
  activate_assets "$backup" "$rollback_sha" "rollback:$backup"
}

case "$COMMAND" in
  status)
    show_status
    exit 0
    ;;
  rollback)
    rollback_latest
    exit 0
    ;;
  deploy)
    ;;
  *)
    die "usage: $0 [deploy [ref]|status|rollback]"
    ;;
esac

[ -d "$SERVE_ROOT/mobile" ] || die "serve root is not a GovPress checkout: $SERVE_ROOT"

if [ ! -f "$CURRENT_SHA_PATH" ] && [ "$ALLOW_DIRTY_STATIC" != "1" ] \
  && git -C "$SERVE_ROOT" rev-parse HEAD >/dev/null 2>&1; then
  dirty_static=$(git -C "$SERVE_ROOT" status --porcelain -- ui mobile/dist)
  [ -z "$dirty_static" ] || die "live static tree has uncommitted changes; set GOVPRESS_WEB_ALLOW_DIRTY_STATIC=1 to adopt it"
fi

build_root=$(mktemp -d "$STATE_ROOT/tmp/build.XXXXXX")
cleanup_build() {
  case "$build_root" in
    "$STATE_ROOT/tmp/build."*) rm -rf -- "$build_root" ;;
  esac
}
trap cleanup_build EXIT

if [ -n "$SOURCE_DIR" ]; then
  source_root=$(cd -- "$SOURCE_DIR" && pwd)
  if [ -n "$EXPECTED_SHA" ]; then
    source_sha="$EXPECTED_SHA"
  else
    source_sha=$(git -C "$source_root" rev-parse HEAD 2>/dev/null || true)
  fi
  [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || die "GOVPRESS_WEB_EXPECT_SHA or a Git source directory is required"
elif [ "$SOURCE_MODE" = "git" ]; then
  [[ "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || die "invalid Git ref: $REF"
  [[ "$REF" != -* && "$REF" != *..* && "$REF" != *@\{* && "$REF" != */ ]] || die "unsafe Git ref: $REF"
  mirror_root="$STATE_ROOT/source.git"
  if [ ! -d "$mirror_root" ]; then
    git init --bare "$mirror_root" >/dev/null
    git --git-dir="$mirror_root" remote add origin "$GIT_URL"
  else
    git --git-dir="$mirror_root" remote set-url origin "$GIT_URL"
  fi
  GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=20}" \
    git --git-dir="$mirror_root" fetch --force --prune --depth=1 origin "$REF"
  source_sha=$(git --git-dir="$mirror_root" rev-parse FETCH_HEAD)
  [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || die "could not resolve an exact source SHA"
elif [ "$SOURCE_MODE" = "api" ]; then
  [ -x "$HELPER" ] || die "source materializer is missing: $HELPER"
  source_sha=$(python3 "$HELPER" --repository "$REPOSITORY" --ref "$REF" --resolve-only)
  [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || die "could not resolve an exact source SHA"
else
  die "GOVPRESS_WEB_SOURCE_MODE must be git or api"
fi

if [ "$(current_sha)" = "$source_sha" ]; then
  echo "deploy_status=no_change"
  echo "source_sha=$source_sha"
  exit 0
fi

if [ -z "$SOURCE_DIR" ]; then
  source_root="$build_root/source"
  mkdir -p "$source_root"
  if [ "$SOURCE_MODE" = "git" ]; then
    git --git-dir="$mirror_root" archive "$source_sha" | tar -x -C "$source_root"
  else
    resolved_sha=$(python3 "$HELPER" --repository "$REPOSITORY" --ref "$source_sha" --destination "$source_root")
    [ "$resolved_sha" = "$source_sha" ] || die "materialized source SHA does not match resolved SHA"
  fi
fi

[ -f "$source_root/ui/landing.html" ] || die "source landing page is missing"
[ -f "$source_root/mobile/package-lock.json" ] || die "source package lock is missing"

if [ "$SKIP_BUILD" != "1" ]; then
  mkdir -p "$STATE_ROOT/npm-cache"
  (
    cd "$source_root/mobile"
    npm ci --cache "$STATE_ROOT/npm-cache"
  )

  if [ -z "${EXPO_PUBLIC_GOVPRESS_API_KEY:-}" ] && [ -f "$SERVE_ROOT/deploy/wsl/.env" ]; then
    EXPO_PUBLIC_GOVPRESS_API_KEY=$(python3 - "$SERVE_ROOT/deploy/wsl/.env" <<'PY'
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

  (
    cd "$source_root/mobile"
    if [ "$RUN_TYPECHECK" = "1" ]; then
      npm run typecheck
    fi
    npm run export:web
  )
fi

asset_tree_is_valid "$source_root" || die "built source does not contain a complete static asset tree"
release_root="$STATE_ROOT/releases/$source_sha"
if [ ! -d "$release_root" ]; then
  release_tmp="$STATE_ROOT/releases/.${source_sha}.$$"
  mkdir -p "$release_tmp/ui" "$release_tmp/mobile/dist"
  rsync -a --delete "$source_root/ui/" "$release_tmp/ui/"
  rsync -a --delete "$source_root/mobile/dist/" "$release_tmp/mobile/dist/"
  printf '%s\n' "$source_sha" > "$release_tmp/source.sha"
  printf '%s\n' "$REF" > "$release_tmp/source.ref"
  printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$release_tmp/built-at"
  mv -- "$release_tmp" "$release_root"
fi

activate_assets "$release_root" "$source_sha" "$REF"
