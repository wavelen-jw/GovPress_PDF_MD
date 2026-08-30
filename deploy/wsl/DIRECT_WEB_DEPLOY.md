# Server W direct web deployment

This path publishes the Readhim landing page and web app without GitHub Actions.
The running host proxy reads `ui/` and `mobile/dist/` on every request, so the
deployer replaces those directories without restarting the API or Cloudflare
Tunnel.

## Install

From a clean checkout on server W:

```bash
deploy/wsl/bin/install_web_direct_deploy.sh --deploy-now
```

The installer copies a stable deployer and GitHub source materializer to
`/home/wavel/.govpress-web/bin`. It also installs a user crontab entry that
checks the private repository's `web` branch every five minutes. The deployer uses a lock, so
manual and scheduled deployments cannot overlap.

The default source mode uses the existing server W SSH key to fetch the private
repository. Verify it with `git ls-remote git@github.com:wavelen-jw/GovPress_PDF_MD.git refs/heads/web`. An API fallback is available by setting
`GOVPRESS_WEB_SOURCE_MODE=api`; in that mode provide `GITHUB_TOKEN` through the
scheduler environment without placing it in the repository or command output.

## Safety model

1. Resolve `web` to an exact 40-character commit SHA through the GitHub SSH endpoint.
2. Exit without building when that SHA is already live.
3. Shallow-fetch the exact SHA and materialize it into a temporary directory.
4. Run `npm ci` from the lockfile and create the Expo web export. An additional
   TypeScript check can be enabled with `GOVPRESS_WEB_RUN_TYPECHECK=1`.
5. Copy immutable assets into `/home/wavel/.govpress-web/releases/<sha>`.
6. Stage both live directories on the same filesystem.
7. Replace `ui/` and `mobile/dist/`, retaining the previous trees as a backup.
8. Compare local and public response hashes with the release landing page and
   compare the local app response with the release app index.
9. Restore both prior trees automatically if any smoke check fails.

The first deployment refuses to adopt an already-modified live static tree.
Use `GOVPRESS_WEB_ALLOW_DIRTY_STATIC=1` only after reviewing and preserving
those changes.

## Operations

```bash
/home/wavel/.govpress-web/bin/deploy_web_direct.sh status
/home/wavel/.govpress-web/bin/deploy_web_direct.sh deploy web
/home/wavel/.govpress-web/bin/deploy_web_direct.sh rollback
tail -f /home/wavel/.govpress-web/logs/deploy.log
```

`rollback` activates the newest retained backup and runs the same smoke checks.
The ten newest backups are retained by default. Override this with
`GOVPRESS_WEB_KEEP_BACKUPS`.

## Test with a local source tree

```bash
GOVPRESS_WEB_SOURCE_DIR=/path/to/clean/checkout \
GOVPRESS_WEB_EXPECT_SHA=<40-character-commit-sha> \
deploy/wsl/bin/deploy_web_direct.sh deploy web
```

This option is intended for controlled recovery and testing. Scheduled
production deployment always resolves the private repository's `web` ref.
