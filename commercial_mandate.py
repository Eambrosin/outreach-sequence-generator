from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

MANDATE_SCHEMA_VERSION = "1.0"

MANDATE_FIELDS = [
    "mandate_schema_version",
    "mandate_id",
    "mandate_name",
    "mandate_status",
    "mandate_client",
    "mandate_corridor",
    "mandate_counterparty_focus",
    "mandate_origin_market",
    "mandate_target_market",
    "mandate_product",
    "mandate_product_category",
    "mandate_commercial_objective",
    "mandate_target_buyer_types",
    "mandate_target_partner_types",
    "mandate_route_to_market",
    "mandate_value_proposition",
    "mandate_known_constraints",
    "mandate_hs_code",
    "mandate_cn_code",
    "mandate_ncm_code",
    "mandate_target_territories",
    "mandate_working_languages",
    "mandate_success_criteria",
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "<na>", "null"}:
        return ""
    return text


@dataclass(frozen=True)
class CommercialMandate:
    mandate_id: str = ""
    mandate_name: str = ""
    mandate_status: str = "Active"
    mandate_client: str = ""
    mandate_corridor: str = ""
    mandate_counterparty_focus: str = "Buyers"
    mandate_origin_market: str = ""
    mandate_target_market: str = ""
    mandate_product: str = ""
    mandate_product_category: str = ""
    mandate_commercial_objective: str = ""
    mandate_target_buyer_types: str = ""
    mandate_target_partner_types: str = ""
    mandate_route_to_market: str = ""
    mandate_value_proposition: str = ""
    mandate_known_constraints: str = ""
    mandate_hs_code: str = ""
    mandate_cn_code: str = ""
    mandate_ncm_code: str = ""
    mandate_target_territories: str = ""
    mandate_working_languages: str = ""
    mandate_success_criteria: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = {
            key: _clean(value)
            for key, value in asdict(self).items()
        }
        payload["mandate_schema_version"] = MANDATE_SCHEMA_VERSION
        return payload


def mandate_from_mapping(row: Mapping[str, Any]) -> dict[str, str]:
    payload = {
        field: _clean(row.get(field, ""))
        for field in MANDATE_FIELDS
    }
    if not payload["mandate_schema_version"]:
        payload["mandate_schema_version"] = MANDATE_SCHEMA_VERSION
    return payload


def apply_mandate_fields(dataframe, mandate: Mapping[str, Any]):
    result = dataframe.copy()
    payload = mandate_from_mapping(mandate)
    for field, value in payload.items():
        result[field] = value
    return result


def has_mandate_context(row: Mapping[str, Any]) -> bool:
    payload = mandate_from_mapping(row)
    return any(
        payload.get(field, "")
        for field in [
            "mandate_id",
            "mandate_name",
            "mandate_client",
            "mandate_corridor",
            "mandate_product",
            "mandate_commercial_objective",
        ]
    )


def mandate_summary(row: Mapping[str, Any]) -> str:
    payload = mandate_from_mapping(row)
    parts = [
        payload.get("mandate_name", ""),
        payload.get("mandate_corridor", ""),
        payload.get("mandate_product", ""),
        payload.get("mandate_target_market", ""),
    ]
    return " · ".join(part for part in parts if part)
