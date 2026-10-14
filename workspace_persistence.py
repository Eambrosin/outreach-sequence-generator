from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

import requests


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "<na>", "null"} else text


def _secret(st, name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return _clean(value) or _clean(os.getenv(name, ""))


def config_from_streamlit(st) -> dict[str, str]:
    return {
        "url": _secret(st, "AMBROSIN_SUPABASE_URL"),
        "key": _secret(st, "AMBROSIN_SUPABASE_KEY"),
        "table": _secret(st, "AMBROSIN_SUPABASE_MANDATES_TABLE") or "commercial_mandates",
    }


def is_enabled(config: Mapping[str, Any]) -> bool:
    return bool(_clean(config.get("url")) and _clean(config.get("key")))


def ensure_mandate_id(mandate: Mapping[str, Any]) -> str:
    return _clean(mandate.get("mandate_id")) or f"mandate_{uuid.uuid4().hex}"


def _headers(config: Mapping[str, Any], merge: bool = False) -> dict[str, str]:
    headers = {
        "apikey": str(config["key"]),
        "Authorization": f"Bearer {config['key']}",
        "Content-Type": "application/json",
    }
    if merge:
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    return headers


def save_mandate(
    config: Mapping[str, Any],
    mandate: Mapping[str, Any],
    source_stage: str,
) -> dict[str, Any]:
    if not is_enabled(config):
        raise RuntimeError("Cloud persistence is not configured.")

    payload = dict(mandate)
    payload["mandate_id"] = ensure_mandate_id(payload)
    payload["mandate_status"] = _clean(payload.get("mandate_status")) or "Active"

    record = {
        "mandate_id": payload["mandate_id"],
        "mandate_name": _clean(payload.get("mandate_name")),
        "mandate_status": payload["mandate_status"],
        "mandate_client": _clean(payload.get("mandate_client")),
        "mandate_target_market": _clean(payload.get("mandate_target_market")),
        "mandate_product": _clean(payload.get("mandate_product")),
        "source_stage": _clean(source_stage).upper(),
        "payload": payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    endpoint = f"{str(config['url']).rstrip('/')}/rest/v1/{config['table']}"
    response = requests.post(
        endpoint,
        params={"on_conflict": "mandate_id"},
        headers=_headers(config, merge=True),
        data=json.dumps(record, ensure_ascii=False),
        timeout=20,
    )
    response.raise_for_status()
    return payload


def list_mandates(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not is_enabled(config):
        return []

    endpoint = f"{str(config['url']).rstrip('/')}/rest/v1/{config['table']}"
    response = requests.get(
        endpoint,
        params={
            "select": "mandate_id,mandate_name,mandate_status,mandate_client,mandate_target_market,mandate_product,payload,updated_at",
            "mandate_status": "eq.Active",
            "order": "updated_at.desc",
            "limit": "100",
        },
        headers=_headers(config),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def load_saved_mandate(st, key_prefix: str) -> dict[str, Any]:
    config = config_from_streamlit(st)
    if not is_enabled(config):
        return {}

    try:
        records = list_mandates(config)
    except Exception as exc:
        st.warning(f"Shared mandate storage unavailable: {exc}")
        return {}

    if not records:
        st.caption("Shared workspace connected. No saved mandates yet.")
        return {}

    labels = ["— Select a saved mandate —"]
    for item in records:
        detail = " · ".join(
            x for x in [
                _clean(item.get("mandate_client")),
                _clean(item.get("mandate_product")),
                _clean(item.get("mandate_target_market")),
            ] if x
        )
        name = _clean(item.get("mandate_name")) or "Unnamed mandate"
        labels.append(f"{name} — {detail}" if detail else name)

    selected = st.selectbox(
        "Saved Commercial Mandate",
        labels,
        key=f"{key_prefix}_saved_mandate",
    )
    if selected == labels[0]:
        return {}

    record = records[labels.index(selected) - 1]
    payload = record.get("payload")
    return dict(payload) if isinstance(payload, dict) else {}


def render_save_control(
    st,
    mandate: Mapping[str, Any],
    source_stage: str,
    key_prefix: str,
) -> dict[str, Any]:
    config = config_from_streamlit(st)
    payload = dict(mandate or {})

    if not is_enabled(config):
        st.caption(
            "Shared cloud persistence is optional. Portable mandate JSON remains available."
        )
        return payload

    if st.button(
        "☁️ Save Commercial Mandate",
        key=f"{key_prefix}_save_mandate",
        use_container_width=True,
    ):
        try:
            payload = save_mandate(config, payload, source_stage)
            st.success("Commercial Mandate saved to the shared workspace.")
        except Exception as exc:
            st.error(f"Could not save Commercial Mandate: {exc}")

    return payload
