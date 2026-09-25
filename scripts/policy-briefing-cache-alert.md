# Policy briefing source withdrawal and retired alert

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

## Monitoring decision

The daily cache checker and its Telegram workflow were retired after the
provider's withdrawal notice was confirmed. The scheduled policy-briefing QC
workflow and its Telegram notification were also disabled. Manual historical
QC remains available without a Telegram alert. The general server monitor now
checks the converter version endpoint instead of the withdrawn catalog; its
scheduled runs do not send Telegram messages. Deployment-failure alerts for
other services remain separate.

The Cloudflare-hosted web bundle uses Server W as its default and Server N as
the next fallback. Retired Server V remains as a legacy choice in the bundle,
but Server W's direct upstream failure does not depend on V or web hosting.

Current-day browsing cannot be restored through this withdrawn source API.
Any future integration must use an independently authorized data source.
