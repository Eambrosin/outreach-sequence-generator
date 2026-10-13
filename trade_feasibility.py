from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

TRADE_FEASIBILITY_SCHEMA_VERSION = "1.0"

TRADE_FEASIBILITY_FIELDS = [
    "trade_feasibility_schema_version",
    "trade_feasibility_status",
    "trade_tariff_scenario_status",
    "trade_preferential_treatment_status",
    "trade_ex_tarifario_status",
    "trade_rules_of_origin_status",
    "trade_import_requirements_status",
    "trade_technical_requirements_status",
    "trade_after_sales_status",
    "trade_feasibility_notes",
    "trade_specialist_validation_notes",
]

ALLOWED_STATUS = {
    "Unknown",
    "To Verify",
    "In Review",
    "Verified",
    "Not Applicable",
}


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
class TradeFeasibility:
    trade_feasibility_status: str = "To Verify"
    trade_tariff_scenario_status: str = "To Verify"
    trade_preferential_treatment_status: str = "To Verify"
    trade_ex_tarifario_status: str = "Unknown"
    trade_rules_of_origin_status: str = "To Verify"
    trade_import_requirements_status: str = "To Verify"
    trade_technical_requirements_status: str = "To Verify"
    trade_after_sales_status: str = "To Verify"
    trade_feasibility_notes: str = ""
    trade_specialist_validation_notes: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = {
            key: _clean(value)
            for key, value in asdict(self).items()
        }
        payload["trade_feasibility_schema_version"] = (
            TRADE_FEASIBILITY_SCHEMA_VERSION
        )
        return payload


def feasibility_from_mapping(row: Mapping[str, Any]) -> dict[str, str]:
    payload = {
        field: _clean(row.get(field, ""))
        for field in TRADE_FEASIBILITY_FIELDS
    }
    if not payload["trade_feasibility_schema_version"]:
        payload["trade_feasibility_schema_version"] = (
            TRADE_FEASIBILITY_SCHEMA_VERSION
        )
    return payload


def apply_trade_feasibility_fields(dataframe, feasibility: Mapping[str, Any]):
    result = dataframe.copy()
    payload = feasibility_from_mapping(feasibility)
    for field, value in payload.items():
        result[field] = value
    return result
