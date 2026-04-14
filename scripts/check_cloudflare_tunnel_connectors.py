from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import subprocess
import sys
from typing import Any


DEFAULT_TUNNELS = {
    "serverH": "b73b8bf8-453e-427d-ad76-02dcb3c7448c",
    "serverW": "4390f5bd-3dbe-49f5-ab52-382de7670294",
}


@dataclass(frozen=True)
class Connector:
    connector_id: str
    created: str
    architecture: str
    version: str
    origin_ip: str
    edge: str

    def created_at(self) -> datetime:
        return datetime.fromisoformat(self.created.replace("Z", "+00:00"))


def parse_tunnel_info(raw: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in raw.splitlines() if line.strip()]
    result: dict[str, Any] = {"name": "", "id": "", "created": "", "connectors": []}
    connector_rows: list[Connector] = []

    for line in lines:
        if line.startswith("NAME:"):
            result["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("ID:"):
            result["id"] = line.split(":", 1)[1].strip()
        elif line.startswith("CREATED:"):
            result["created"] = line.split(":", 1)[1].strip()
        elif line.startswith("CONNECTOR ID") or line.startswith("CREATED") or line.startswith("ARCHITECTURE"):
            continue
        elif len(line) >= 36 and "-" in line[:36]:
            parts = line.split()
            if len(parts) < 6:
                continue
            connector_rows.append(
                Connector(
                    connector_id=parts[0],
                    created=parts[1],
                    architecture=parts[2],
                    version=parts[3],
                    origin_ip=parts[4],
                    edge=" ".join(parts[5:]),
                )
            )

    result["connectors"] = [
        {
            "connector_id": item.connector_id,
            "created": item.created,
            "architecture": item.architecture,
            "version": item.version,
            "origin_ip": item.origin_ip,
            "edge": item.edge,
        }
        for item in connector_rows
    ]
    return result


def sort_connectors(connectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        connectors,
        key=lambda item: datetime.fromisoformat(str(item["created"]).replace("Z", "+00:00")),
        reverse=True,
    )


def stale_connector_ids(connectors: list[dict[str, Any]]) -> list[str]:
    ordered = sort_connectors(connectors)
    return [item["connector_id"] for item in ordered[1:]]


def run_cloudflared(*args: str) -> str:
    result = subprocess.run(
        ["cloudflared", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def inspect_tunnel(name: str, tunnel_id: str, *, cleanup_stale: bool) -> dict[str, Any]:
    info = parse_tunnel_info(run_cloudflared("tunnel", "info", tunnel_id))
    stale_ids = stale_connector_ids(info["connectors"])
    cleaned: list[str] = []
    if cleanup_stale:
        for connector_id in stale_ids:
            run_cloudflared("tunnel", "cleanup", "--connector-id", connector_id, tunnel_id)
            cleaned.append(connector_id)
        if cleaned:
            info = parse_tunnel_info(run_cloudflared("tunnel", "info", tunnel_id))
            stale_ids = stale_connector_ids(info["connectors"])
    return {
        "key": name,
        "tunnel_id": tunnel_id,
        "name": info["name"],
        "connectors": sort_connectors(info["connectors"]),
        "stale_connector_ids": stale_ids,
        "cleaned_connector_ids": cleaned,
        "healthy_connector_count": len(info["connectors"]) - len(stale_ids),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and optionally clean stale Cloudflare tunnel connectors")
    parser.add_argument(
        "--tunnel",
        choices=["serverH", "serverW", "all"],
        default="all",
        help="Tunnel to inspect. Defaults to all managed tunnels.",
    )
    parser.add_argument("--cleanup-stale", action="store_true", help="Remove all but the newest connector per tunnel")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    tunnel_items = DEFAULT_TUNNELS.items() if args.tunnel == "all" else [(args.tunnel, DEFAULT_TUNNELS[args.tunnel])]
    payload = {
        "tunnels": [inspect_tunnel(name, tunnel_id, cleanup_stale=args.cleanup_stale) for name, tunnel_id in tunnel_items]
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in payload["tunnels"]:
            print(f"{item['key']} {item['name']} tunnel={item['tunnel_id']}")
            print(f"  connectors={len(item['connectors'])} stale={len(item['stale_connector_ids'])}")
            if item["stale_connector_ids"]:
                print(f"  stale_connector_ids={', '.join(item['stale_connector_ids'])}")
            if item["cleaned_connector_ids"]:
                print(f"  cleaned_connector_ids={', '.join(item['cleaned_connector_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
