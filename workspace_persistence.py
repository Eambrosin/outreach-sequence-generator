from __future__ import annotations

import hmac
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
        "access_token": _secret(st, "AMBROSIN_WORKSPACE_ACCESS_TOKEN"),
        "table": _secret(st, "AMBROSIN_SUPABASE_MANDATES_TABLE") or "commercial_mandates",
    }


def missing_config_fields(config: Mapping[str, Any]) -> list[str]:
    missing = []
    if not _clean(config.get("url")):
        missing.append("AMBROSIN_SUPABASE_URL")
    if not _clean(config.get("key")):
        missing.append("AMBROSIN_SUPABASE_KEY")
    if not _clean(config.get("access_token")):
        missing.append("AMBROSIN_WORKSPACE_ACCESS_TOKEN")
    return missing


def is_enabled(config: Mapping[str, Any]) -> bool:
    return not missing_config_fields(config)


def workspace_access_granted(st, key_prefix: str) -> bool:
    config = config_from_streamlit(st)
    if not is_enabled(config):
        return False

    session_key = f"{key_prefix}_workspace_authorized"
    if st.session_state.get(session_key):
        return True

    entered = st.text_input(
        "Private Workspace Access",
        type="password",
        key=f"{key_prefix}_workspace_access_input",
        help=(
            "Required to read or write the private Ambrosin cloud workspace. "
            "This token is separate from the database credential."
        ),
    )
    if not entered:
        return False

    if hmac.compare_digest(
        str(entered),
        str(config["access_token"]),
    ):
        st.session_state[session_key] = True
        st.success("Private Workspace access granted.")
        return True

    st.error("Invalid Private Workspace access token.")
    return False


def ensure_mandate_id(mandate: Mapping[str, Any]) -> str:
    return _clean(mandate.get("mandate_id")) or f"mandate_{uuid.uuid4().hex}"


def _headers(config: Mapping[str, Any], merge: bool = False) -> dict[str, str]:
    headers = {
        "apikey": str(config["key"]),
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


def get_mandate_by_id(
    config: Mapping[str, Any],
    mandate_id: str,
) -> dict[str, Any]:
    if not is_enabled(config):
        return {}

    mandate_id = _clean(mandate_id)
    if not mandate_id:
        return {}

    endpoint = f"{str(config['url']).rstrip('/')}/rest/v1/{config['table']}"
    response = requests.get(
        endpoint,
        params={
            "select": "mandate_id,mandate_name,mandate_status,mandate_client,mandate_target_market,mandate_product,payload,updated_at",
            "mandate_id": f"eq.{mandate_id}",
            "limit": "1",
        },
        headers=_headers(config),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list) or not data:
        return {}

    record = data[0]
    payload = record.get("payload")
    result = dict(payload) if isinstance(payload, dict) else {}
    result["mandate_id"] = _clean(record.get("mandate_id")) or mandate_id
    return result


def _query_mandate_id(st) -> str:
    try:
        value = st.query_params.get("mandate_id", "")
    except Exception:
        return ""

    if isinstance(value, list):
        value = value[0] if value else ""
    return _clean(value)


def load_saved_mandate(st, key_prefix: str) -> dict[str, Any]:
    config = config_from_streamlit(st)
    missing = missing_config_fields(config)
    if missing:
        st.warning(
            "Private Workspace is not configured. Missing Streamlit secret(s): "
            + ", ".join(missing)
        )
        return {}

    if not workspace_access_granted(st, key_prefix):
        st.caption(
            "Cloud mandate handoff is protected. Enter Private Workspace Access to enable it."
        )
        return {}

    query_mandate_id = _query_mandate_id(st)
    if query_mandate_id:
        try:
            resolved = get_mandate_by_id(
                config,
                query_mandate_id,
            )
        except Exception as exc:
            st.warning(
                f"Could not resolve mandate {query_mandate_id}: {exc}"
            )
            resolved = {}

        if resolved:
            st.session_state[
                f"{key_prefix}_active_mandate_id"
            ] = query_mandate_id
            st.success(
                "Commercial Mandate loaded automatically from the shared workspace."
            )
            return resolved

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

    missing = missing_config_fields(config)
    if missing:
        st.caption(
            "Cloud persistence is not active. Missing Streamlit secret(s): "
            + ", ".join(missing)
        )
        return payload

    if not st.session_state.get(
        f"{key_prefix}_workspace_authorized"
    ):
        st.caption(
            "Enter Private Workspace Access above to enable cloud save/update."
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
