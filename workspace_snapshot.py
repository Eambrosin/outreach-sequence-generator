from __future__ import annotations

from datetime import date, datetime, timezone
import json
import math
import re
from typing import Any, Mapping, Sequence

WORKSPACE_SNAPSHOT_SCHEMA_VERSION = "1.0"


def _json_safe(value: Any):
    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass

    try:
        if value != value:
            return None
    except Exception:
        pass

    return str(value)


def build_workspace_snapshot(
    *,
    mandate: Mapping[str, Any] | None,
    pipeline_records: Sequence[Mapping[str, Any]] | None,
    execution_updates: Sequence[Mapping[str, Any]] | None = None,
    deal_sheets: Sequence[Mapping[str, Any]] | None = None,
    field_visit_feedback: Sequence[Mapping[str, Any]] | None = None,
    source_name: str = "",
) -> dict[str, Any]:
    return {
        "workspace_snapshot_schema_version": WORKSPACE_SNAPSHOT_SCHEMA_VERSION,
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_stage": "ENGAGE",
        "source_name": str(source_name or "").strip(),
        "mandate": _json_safe(dict(mandate or {})),
        "pipeline": _json_safe(list(pipeline_records or [])),
        "execution_updates": _json_safe(list(execution_updates or [])),
        "deal_sheets": _json_safe(list(deal_sheets or [])),
        "field_visit_feedback": _json_safe(list(field_visit_feedback or [])),
    }


def snapshot_to_json(snapshot: Mapping[str, Any], *, indent: int = 2) -> str:
    return json.dumps(
        _json_safe(dict(snapshot)),
        ensure_ascii=False,
        indent=indent,
    )


def snapshot_from_json(payload: str | bytes) -> dict[str, Any]:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    data = json.loads(str(payload))
    if not isinstance(data, dict):
        raise ValueError("Workspace Snapshot JSON must contain one object.")

    version = str(
        data.get("workspace_snapshot_schema_version", "")
    ).strip()
    if version != WORKSPACE_SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported Workspace Snapshot schema version: "
            + (version or "missing")
        )

    normalized = {
        "workspace_snapshot_schema_version": version,
        "exported_at_utc": str(data.get("exported_at_utc", "") or ""),
        "source_stage": str(data.get("source_stage", "") or ""),
        "source_name": str(data.get("source_name", "") or ""),
        "mandate": data.get("mandate") if isinstance(data.get("mandate"), dict) else {},
        "pipeline": data.get("pipeline") if isinstance(data.get("pipeline"), list) else [],
        "execution_updates": (
            data.get("execution_updates")
            if isinstance(data.get("execution_updates"), list)
            else []
        ),
        "deal_sheets": (
            data.get("deal_sheets")
            if isinstance(data.get("deal_sheets"), list)
            else []
        ),
        "field_visit_feedback": (
            data.get("field_visit_feedback")
            if isinstance(data.get("field_visit_feedback"), list)
            else []
        ),
    }
    return normalized


def snapshot_filename(snapshot: Mapping[str, Any]) -> str:
    mandate = snapshot.get("mandate", {}) or {}
    base = (
        mandate.get("mandate_name")
        or mandate.get("mandate_client")
        or mandate.get("mandate_product")
        or "commercial_mandate"
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(base)).strip("_").lower()
    return f"{slug or 'commercial_mandate'}_workspace_snapshot.json"
