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
  The replacement URL and any provider notice have not been verified.
- Server W's direct API `/health` returns 200. Its host proxy `/health` probes
  today's policy catalog and returns 502 when that catalog fails. Historical
  cached lists still work (September 14 returned 77 items over the public API).

## Daily refresh and alert

`.github/workflows/daily-policy-briefing-cache.yml` runs at 22:15 KST and may
also be dispatched manually. It calls Server W's authenticated `today` API for
the current Seoul date. This request refreshes the server's catalog when due.
The check rejects HTTP errors, missing or mismatched dates, incomplete responses
and `served_stale`. Failures send one Telegram alert using the existing
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` repository secrets; the workflow
fails if delivery is not confirmed. The API key is sent only in an HTTP header.
Neither key is printed or written to the repository.

Verify an activated workflow with a manual dispatch and inspect its result,
then check the next scheduled run. Repository Actions are enabled and the bot
secrets exist, but the previously scheduled QC and health workflows have **no
runs after July 30, 2026**. A schedule declaration alone does not prove the
notification is operating. This workflow must be present on the default `web`
branch before it can run; deployment of the API service is a separate operation.

The source API replacement remains necessary to restore current-day browsing.
This monitor detects the outage and prevents silent cache failure; it cannot
repair a withdrawn or changed upstream endpoint.
