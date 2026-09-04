# Server V retirement runbook

Status: api2 cutover passed; 24-hour observation started at 2026-09-05 00:42 KST

Started: 2026-09-05 (Asia/Seoul)

This runbook retires the Naver Cloud server V without breaking existing
GovPress clients. Irreversible cleanup is allowed only after every gate below
passes.

## Fixed decisions

- W and N remain the active API servers.
- api2.govpress.cloud remains as a compatibility hostname for old clients and
  points to the same W origin as api4.govpress.cloud.
- api2 must not use an HTTP redirect because uploads and authenticated POST
  requests must keep their method and headers.
- ai.govpress.cloud is unused and its DNS record and repository implementation are deleted.
- ssh-v.govpress.cloud and all V credentials stay available through the
  rollback window.
- A stopped V server is a short rollback measure, not a cost-saving state.

## Audited state

- Server type: Naver Cloud KVM mi1-g3_MICRO
- Root storage: 50 GB ext4, about 17 GB used
- App storage: about 21 MB
- App config: about 8 KB
- Legacy GovWork files: about 38 MB
- jobs.sqlite3 rows: 0
- W runtime govpress-hwpx-md: v0.4.10
- N and W public/local health: HTTP 200 at audit time
- V API tunnel: govpress-api-naver
  (504eb280-e45e-470b-801b-8b3b71c39ac9)
- V SSH tunnel: govpress-v-ssh
  (afb85d93-ca96-4854-bcbc-cb667257ef30)
- W compatibility ingress tunnel: govpress-w-ssh
  (f8e2fdf2-9f58-4ae2-876f-54652b1431ff)
- api2-canary.govpress.cloud currently points to the W compatibility ingress
  tunnel. The W ingress is also ready to accept api2.govpress.cloud.
- V outbound SSH public-key fingerprint:
  SHA256:QvGi96HvWcLe9/Vq6e9pyK/iGxcGY+vxTt9E4gvFbdY

## Gate 1: source and CI

- [x] Remove serverV from mobile/src/constants.ts.
- [x] Remove deploy-v and all V dependencies from vps.yml.
- [x] Keep converter and policy smoke tests working with W/N.
- [x] Remove V-only SSH-key, cache, and shortener workflow paths.
- [x] Update OpenClaw and health-monitor fallbacks to W/N.
- [x] Pass focused Python tests and workflow syntax checks.
- [x] Push a branch and review the complete diff.
- [ ] Merge only after the api2 canary passes.

## Gate 2: file backup

Create two copies outside V and verify checksums for:

- /home/wavel/GovPress_PDF_MD/storage
- /home/wavel/GovPress_PDF_MD/config
- /home/wavel/.local/share/govwork
- relevant systemd and Caddy configuration
- service/package/firewall inventory
- recent service logs

Store .env, Tunnel credentials, Access tokens, and private SSH keys only in an
encrypted secret bundle. Do not place them in the normal archive or Git.

Required checks:

- [x] sqlite PRAGMA integrity_check returns ok.
- [x] queued and processing job counts are zero.
- [x] normal archive SHA-256 is recorded.
- [x] both copies exist outside V.
- [x] one copy is restored into a temporary directory successfully.

Backup evidence recorded on 2026-09-05:

- Normal archive: server-v-normal-20260905T1530Z.tar.gz
- Normal archive SHA-256:
  1aa7a68026efccd8c1e6f09a4324ac5661d38494841bbc8cccc3d5becc4622af
- Encrypted secret bundle: server-v-secrets-20260905T1530Z.tar.gz.gpg
- Encrypted bundle SHA-256:
  6dfd3826341d5bf75523eafecf96c1aa0df4d14fb203e6e27ff8180bf7602d80
- Verified copies are on W and N under
  backups/server-v-retirement/2026-09-05.
- The decryption passphrase is stored separately on the jump host with mode
  0600 and was not copied with either encrypted bundle.
- A temporary W restore passed the archive manifest, SQLite integrity check,
  and zero-job check.

## Gate 3: Cloudflare canary and cutover

1. Create api2-canary.govpress.cloud on the W compatibility ingress tunnel.
2. Test health, CORS OPTIONS, API-key authentication, a small upload,
   conversion completion, and result download.
3. Repoint api2.govpress.cloud from govpress-api-naver to the W application
   origin through the compatibility ingress tunnel.
4. Repeat the same checks on api2.govpress.cloud.
5. Delete the unused ai.govpress.cloud DNS record and repository implementation.
6. Keep the old V tunnel definitions intact for rollback.

Pass conditions:

- [x] api4, api5, api2-canary, and api2 health all return 200.
- [x] W/N report govpress-hwpx-md v0.4.10.
- [x] Conversion output hashes match across W/N.
- [x] A real authenticated upload succeeds through api2.
- [x] ai.govpress.cloud has no DNS record or deployment path.
- [ ] The scheduled monitor and W/N deploy workflows pass.

Canary evidence recorded on 2026-09-05:

- api2-canary health returned HTTP 200.
- CORS preflight returned HTTP 204 and allowed the GovPress origin, POST, and
  the required API headers.
- An upload without an API key was rejected with HTTP 401.
- A valid 66 KB HWPX upload, job poll, and result download all returned HTTP
  200, and the job completed.
- The returned text and HTML Markdown SHA-256 were both
  8d653e4edca88e4958faa4b16d59250644203060477cf5d53d2b64249cbb9b4a.
- W and N both reported govpress-hwpx-md v0.4.10 and completed the same valid
  sample with hashes identical to the canary result.
- Mobile TypeScript type checking passed.

Cutover evidence recorded on 2026-09-05:

- api2 DNS moved to govpress-w-ssh at 00:42 KST.
- api2 returned health 200, CORS preflight 204, and unauthenticated upload 401.
- An authenticated HWPX job completed through api2 and matched api4 hashes.
- Before cutover, V local API ports accepted TCP but timed out; its database
  integrity was ok with zero total and active jobs.
- The unused ai.govpress.cloud CNAME was deleted through the Cloudflare API;
  an exact-name API query then returned zero records.
- A temporary W redirect service and ingress prepared before the deletion
  decision were removed.
- Do not stop V before 2026-09-06 00:42 KST and before CI gates pass.

## Gate 4: drain and stop

After cutover, leave V running but out of the normal traffic path for at least
24 hours.

- [ ] No legitimate authenticated request reaches V.
- [ ] jobs.sqlite3 remains empty.
- [ ] W/N error rate and latency remain normal.
- [ ] No workflow, client, or operator still needs ssh-v.

Then stop application services, run sync, and stop the server from the Naver
Cloud console. Keep the server, root storage, public IP, V tunnels, and
credentials for a 72-hour fast rollback window.

## Rollback

Rollback immediately if an old client fails, an authenticated api2 conversion
fails, W/N deployment or smoke tests fail, required V-only data is found, or
W/N capacity becomes unsafe.

1. Verify api4 and the W compatibility tunnel before changing DNS.
2. For a W ingress regression, restore the W config backup named
   govpress-w-ssh.yml.bak-retire-v-ai-20260905 and restart the connector.
3. If W is unavailable, add api2 to N, test it through a canary hostname, and
   only then route api2 to the serverN-api5 tunnel.
4. Use V only as a last resort: start or repair it and pass an authenticated
   conversion before routing api2 back to govpress-api-naver.
5. Revert the retirement PR if V deployment automation is required.
6. Record the trigger before resuming the observation window.

## Gate 5: irreversible cleanup

Only after 72 hours of successful stopped-server observation:

- [ ] Create a snapshot of the stopped 50 GB root storage.
- [ ] Wait until the snapshot is fully available.
- [ ] Confirm that no additional storage is attached.
- [ ] Detach the Naver Cloud public IP from V.
- [ ] Explicitly return the public IP.
- [ ] Return the stopped V server.
- [ ] Remove ssh-v.govpress.cloud and delete the V SSH tunnel.
- [ ] Delete the V API tunnel after api2 is confirmed on W.
- [ ] Revoke the V SSH fingerprint from W and N authorized_keys.
- [ ] Remove V-only GitHub secrets and variables.
- [ ] Remove V from Cloud Insight alarms and dashboards.
- [ ] Confirm that Server, Block Storage, and Public IP charges disappear.

Do not delete shared CF_ACCESS_CLIENT_ID, CF_ACCESS_CLIENT_SECRET, API,
Telegram, or converter secrets while W/N still use them.

Keep the final NCP snapshot for 14 days. Restore-test the small file backup
once more, then delete the snapshot and record the deletion date.
