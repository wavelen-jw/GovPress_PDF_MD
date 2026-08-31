#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-status}"
if [ "$#" -gt 0 ]; then
  shift
fi

RUNNER_ROOT="${GOVPRESS_PAGES_RUNNER_ROOT:-/home/ubuntu/.govpress-pages-runner}"
PROJECT="${GOVPRESS_PAGES_PROJECT:-readhim-web}"
PRODUCTION_BRANCH="${GOVPRESS_PAGES_PRODUCTION_BRANCH:-web}"
NODE_ROOT="${GOVPRESS_PAGES_NODE_ROOT:-$RUNNER_ROOT/node-v22.22.1-linux-x64}"
WRANGLER_ROOT="${GOVPRESS_PAGES_WRANGLER_ROOT:-$RUNNER_ROOT/wrangler}"
WRANGLER="$WRANGLER_ROOT/node_modules/.bin/wrangler"

die() {
  echo "pages_runner_n: $*" >&2
  exit 1
}

case "$RUNNER_ROOT" in
  ""|/|/home|/home/ubuntu) die "GOVPRESS_PAGES_RUNNER_ROOT is too broad: $RUNNER_ROOT" ;;
esac

[ -x "$NODE_ROOT/bin/node" ] || die "Node 22 runtime is missing: $NODE_ROOT"
[ -x "$WRANGLER" ] || die "Wrangler is missing: $WRANGLER"
export PATH="$NODE_ROOT/bin:/usr/bin:/bin"

mkdir -p "$RUNNER_ROOT/locks"
exec 9>"$RUNNER_ROOT/locks/pages.lock"
flock -n 9 || die "another Pages operation is already running"

release_for_sha() {
  local sha="${1:-}"
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "an exact 40-character commit SHA is required"
  local release="$RUNNER_ROOT/releases/$sha"
  [ -f "$release/index.html" ] || die "release root index is missing: $release"
  [ -f "$release/app/index.html" ] || die "release app index is missing: $release"
  [ -d "$release/app/_expo" ] || die "release app bundle is missing: $release"
  [ -f "$release/source.sha" ] || die "release source marker is missing: $release"
  [ "$(tr -d '[:space:]' < "$release/source.sha")" = "$sha" ] \
    || die "release source marker does not match $sha"
  echo "$release"
}

show_status() {
  echo "runner_root=$RUNNER_ROOT"
  echo "project=$PROJECT"
  echo "production_branch=$PRODUCTION_BRANCH"
  echo "node_version=$("$NODE_ROOT/bin/node" --version)"
  echo "wrangler_version=$("$WRANGLER" --version)"
  echo "deployment_mode=manual_only"
  echo "oauth_state_present=$([ -d /home/ubuntu/.config/.wrangler ] && echo yes || echo no)"
  find "$RUNNER_ROOT/releases" -mindepth 1 -maxdepth 1 -type d -printf 'release=%f\n' 2>/dev/null | sort
}

case "$COMMAND" in
  status)
    show_status
    ;;
  auth)
    "$WRANGLER" whoami
    ;;
  login)
    "$WRANGLER" login --device
    ;;
  create-project)
    [ "${GOVPRESS_PAGES_CONFIRM_PROJECT:-}" = "$PROJECT" ] \
      || die "set GOVPRESS_PAGES_CONFIRM_PROJECT=$PROJECT to create the project"
    "$WRANGLER" pages project create "$PROJECT" --production-branch "$PRODUCTION_BRANCH"
    ;;
  preview)
    sha="${1:-}"
    release=$(release_for_sha "$sha")
    "$WRANGLER" pages deploy "$release" \
      --project-name "$PROJECT" \
      --branch "preview-${sha:0:12}" \
      --commit-hash "$sha" \
      --commit-message "Manual preview $sha"
    ;;
  production)
    sha="${1:-}"
    release=$(release_for_sha "$sha")
    [ "${GOVPRESS_PAGES_CONFIRM_SHA:-}" = "$sha" ] \
      || die "set GOVPRESS_PAGES_CONFIRM_SHA=$sha to deploy production"
    "$WRANGLER" pages deploy "$release" \
      --project-name "$PROJECT" \
      --branch "$PRODUCTION_BRANCH" \
      --commit-hash "$sha" \
      --commit-message "Manual production $sha"
    ;;
  *)
    die "usage: $0 [status|auth|login|create-project|preview SHA|production SHA]"
    ;;
esac
