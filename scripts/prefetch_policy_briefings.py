from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.adapters.policy_briefing import PolicyBriefingCache, PolicyBriefingCatalog, PolicyBriefingClient


def main() -> int:
    storage_root = Path(
        os.environ.get("GOVPRESS_STORAGE_ROOT", PROJECT_ROOT / "storage")
    )
    client = PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY"))
    if not client.configured:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not configured")

    catalog = PolicyBriefingCatalog(client=client, cache_path=storage_root / "policy_briefing_catalog.json")
    cache = PolicyBriefingCache(client=client, cache_dir=storage_root / "policy_briefing_cache")

    today = date.today()
    items = catalog.refresh_today(today)
    warmed = 0
    skipped = 0
    for item in items:
        if cache.get(item.news_item_id) is not None:
            skipped += 1
            continue
        cache.warm_item(item)
        warmed += 1

    print(f"date={today.isoformat()} total={len(items)} warmed={warmed} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
