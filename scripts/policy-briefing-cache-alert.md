# Policy briefing source outage and daily alert

## Observed outage window

- Server W cache last refreshed `2026-09-14T04:11:37Z` (77 items for September 14).
- The same API container first logged a policy-list 502 on
  `2026-09-18T08:33:03Z` (`2026-09-18 17:33:03` KST).
- There are no Server W policy-list requests or cache files for September 15-17.
  The exact first failing day is therefore unknown; the supported window is
  after September 14's success and no later than September 18's first failure.
- September 24's source request returns HTTP 400 with
  `NO_OPENAPI_SERVICE_ERROR`, reason code `12`, and
  `해당 오픈API 서비스가 없거나 폐기됨`. A deliberately invalid test key returns the
  same code from Server W and a separate network. This indicates a service URL
  registration/availability problem, not evidence of an expired service key.
  The public-data portal announced the withdrawal on June 18, 2026:
  https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004771
  It cites difficulty verifying copyright ownership and usage permission because
  the producing and managing institutions are separate. It directs users to
  each ministry's website instead of a replacement API.
- Server W's direct API `/health` returns 200. Its host proxy `/health` probes
  today's policy catalog and returns 502 when that catalog fails. Historical
  cached lists still work (September 14 returned 77 items over the public API).

## Manual refresh and alert

`.github/workflows/daily-policy-briefing-cache.yml` is manual-only since the
source API was formally withdrawn; scheduled failures would repeatedly alert
without an actionable recovery. When dispatched, it opens an encrypted SSH tunnel to Server W and
calls the authenticated local `today` API for the current Seoul date. The
public API URL is blocked for GitHub runners by a browser-signature rule and
cannot be used for this monitor. The request refreshes the catalog when due.
The check rejects HTTP errors, missing or mismatched dates, incomplete responses
and `served_stale`. Failures send one Telegram alert using the existing
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` repository secrets; the workflow
fails if delivery is not confirmed. The API key is sent only in an HTTP header.
Neither key is printed or written to the repository.

The workflow is available on the default `web` branch. A manual run on September
24, 2026 reached Server W through the SSH tunnel, received `HTTP 502: HTTP
Error 400: Bad Request` from its policy catalog, and logged `telegram_sent`.
The job fails by design when the source fails. Daily scheduling was removed
after the official notice was verified. Deployment of the API service is a
separate operation.

The Cloudflare-hosted web bundle uses Server W as its default and Server N as
the next fallback. Retired Server V remains as a legacy choice in the bundle,
but Server W's direct upstream failure does not depend on V or web hosting.

Current-day browsing cannot be restored through this withdrawn source API.
Any future integration must use an independently authorized data source.
