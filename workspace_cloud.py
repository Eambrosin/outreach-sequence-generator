from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any, Mapping

import requests

from workspace_persistence import (
    config_from_streamlit,
    ensure_mandate_id,
    is_enabled,
    save_mandate,
)


DEFAULT_WORKSPACES_TABLE = "commercial_workspaces"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "<na>", "null"} else text


def workspace_table_from_streamlit(st) -> str:
    try:
        value = st.secrets.get("AMBROSIN_SUPABASE_WORKSPACES_TABLE", "")
    except Exception:
        value = ""
    return (
        _clean(value)
        or _clean(os.getenv("AMBROSIN_SUPABASE_WORKSPACES_TABLE", ""))
        or DEFAULT_WORKSPACES_TABLE
    )


def _headers(config: Mapping[str, Any], merge: bool = False) -> dict[str, str]:
    key = str(config["key"]).strip()
    headers = {
        "apikey": key,
        "Content-Type": "application/json",
    }

    if key.count(".") == 2:
        headers["Authorization"] = f"Bearer {key}"

    if merge:
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    return headers


def build_workspace_record(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(snapshot or {})
    mandate = payload.get("mandate")
    mandate = dict(mandate) if isinstance(mandate, Mapping) else {}

    mandate_id = ensure_mandate_id(mandate)
    mandate["mandate_id"] = mandate_id
    payload["mandate"] = mandate

    workspace_name = (
        _clean(mandate.get("mandate_name"))
        or _clean(mandate.get("mandate_client"))
        or _clean(mandate.get("mandate_product"))
        or "Commercial Mandate"
    )

    return {
        "workspace_id": f"workspace_{mandate_id}",
        "mandate_id": mandate_id,
        "workspace_name": workspace_name,
        "payload": payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_workspace(
    config: Mapping[str, Any],
    table: str,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    if not is_enabled(config):
        raise RuntimeError("Cloud persistence is not configured.")

    record = build_workspace_record(snapshot)

    save_mandate(
        config,
        record["payload"].get("mandate", {}),
        source_stage="ENGAGE",
    )

    endpoint = f"{str(config['url']).rstrip('/')}/rest/v1/{table}"
    response = requests.post(
        endpoint,
        params={"on_conflict": "workspace_id"},
        headers=_headers(config, merge=True),
        data=json.dumps(record, ensure_ascii=False),
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list) and data:
        saved = data[0]
    elif isinstance(data, dict):
        saved = data
    else:
        saved = record

    payload = saved.get("payload")
    return dict(payload) if isinstance(payload, Mapping) else dict(record["payload"])


def list_workspaces(
    config: Mapping[str, Any],
    table: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not is_enabled(config):
        return []

    endpoint = f"{str(config['url']).rstrip('/')}/rest/v1/{table}"
    response = requests.get(
        endpoint,
        params={
            "select": "workspace_id,mandate_id,workspace_name,payload,updated_at",
            "order": "updated_at.desc",
            "limit": str(max(1, min(int(limit), 500))),
        },
        headers=_headers(config),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def workspace_label(record: Mapping[str, Any]) -> str:
    name = _clean(record.get("workspace_name")) or "Commercial Mandate"
    updated = _clean(record.get("updated_at"))
    if updated:
        updated = updated[:16].replace("T", " ")
        return f"{name} — {updated} UTC"
    return name


def cloud_settings(st) -> tuple[dict[str, str], str]:
    return config_from_streamlit(st), workspace_table_from_streamlit(st)
