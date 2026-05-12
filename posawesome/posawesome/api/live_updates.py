from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import frappe
from frappe.utils import cstr

try:
    from werkzeug.wrappers import Response
except Exception:  # pragma: no cover - fallback for isolated test environments
    class Response:  # type: ignore[override]
        def __init__(self, response=None, mimetype=None):
            self.response = response
            self.mimetype = mimetype
            self.headers = {}

from posawesome.posawesome.api.items import get_delta_items
from posawesome.posawesome.api.utils import _ensure_pos_profile, get_active_pos_profile


def _resolve_profile(pos_profile: Any = None) -> Dict[str, Any]:
    if pos_profile:
        try:
            profile, _ = _ensure_pos_profile(pos_profile)
            return profile
        except Exception:
            pass

    active_profile = get_active_pos_profile()
    if active_profile:
        return active_profile
    raise frappe.ValidationError("pos_profile is required")


def _parse_cursor(cursor: Optional[str]) -> Optional[str]:
    text = cstr(cursor or "").strip()
    if not text:
        return None
    return text


def _current_cursor() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_stock_payload(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = []
    for row in rows or []:
        if not row or not row.get("item_code"):
            continue
        items.append(
            {
                "item_code": row.get("item_code"),
                "warehouse": row.get("warehouse"),
                "company": row.get("company"),
                "actual_qty": row.get("actual_qty"),
            }
        )

    return {
        "items": items,
        "item_codes": sorted({row["item_code"] for row in items if row.get("item_code")}),
        "warehouses": sorted({row["warehouse"] for row in items if row.get("warehouse")}),
        "companies": sorted({row["company"] for row in items if row.get("company")}),
        "source_doctype": "Bin",
    }


def _format_sse_event(event: str, payload: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


def _iter_item_update_events(
    profile: Dict[str, Any],
    cursor: Optional[str],
    price_list: Optional[str],
    customer: Optional[str],
    poll_interval: int = 5,
    heartbeat_interval: int = 30,
    limit: int = 200,
):
    last_cursor = _parse_cursor(cursor) or _current_cursor()
    last_heartbeat = time.monotonic()

    yield ": connected\n\n"

    while True:
        try:
            rows = get_delta_items(
                json.dumps(profile),
                modified_after=last_cursor,
                price_list=price_list,
                customer=customer,
                limit=limit,
            ) or []
        except Exception as exc:
            yield _format_sse_event("posawesome_error", {"message": str(exc)})
            time.sleep(max(1, poll_interval))
            continue

        if rows:
            payload = build_stock_payload(rows)
            payload["items"] = rows
            yield _format_sse_event("posa_stock_changed", payload)

            latest_modified = None
            for row in rows:
                modified = cstr(row.get("modified") or "").strip()
                if modified and (latest_modified is None or modified > latest_modified):
                    latest_modified = modified
            if latest_modified:
                last_cursor = latest_modified

        now = time.monotonic()
        if now - last_heartbeat >= heartbeat_interval:
            yield ": heartbeat\n\n"
            last_heartbeat = now

        time.sleep(max(1, poll_interval))


@frappe.whitelist()
def stream_item_updates(
    pos_profile=None,
    cursor=None,
    price_list=None,
    customer=None,
    poll_interval=5,
    heartbeat_interval=30,
    limit=200,
):
    profile = _resolve_profile(pos_profile)

    try:
        poll_interval = max(1, int(poll_interval or 5))
    except (TypeError, ValueError):
        poll_interval = 5

    try:
        heartbeat_interval = max(10, int(heartbeat_interval or 30))
    except (TypeError, ValueError):
        heartbeat_interval = 30

    try:
        limit = max(1, min(int(limit or 200), 1000))
    except (TypeError, ValueError):
        limit = 200

    response = Response(
        _iter_item_update_events(
            profile,
            cursor=cursor,
            price_list=price_list,
            customer=customer,
            poll_interval=poll_interval,
            heartbeat_interval=heartbeat_interval,
            limit=limit,
        ),
        mimetype="text/event-stream",
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response
