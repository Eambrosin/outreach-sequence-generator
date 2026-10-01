from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


OUTCOME_SIGNALS = {
    "Discovery completed": ("warm", "verified"),
    "Follow-up scheduled": ("warm", "verified"),
    "Demo requested": ("hot", "verified"),
    "Proposal requested": ("hot", "verified"),
    "Internal evaluation": ("warm", "verified"),
    "No current timing": ("cold", "verified"),
    "Not a fit": ("cold", "verified"),
    "Could not meet decision-maker": ("cold", "unverified"),
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def build_visit_feedback(
    account: dict,
    *,
    outcome: str,
    needs_summary: str = "",
    patient_demand: str = "",
    current_technologies: str = "",
    decision_process: str = "",
    investment_timing: str = "",
    product_interest: str = "",
    estimated_value_eur: float = 0.0,
    next_action: str = "",
    notes: str = "",
    visit_date: str = "",
) -> dict:
    """
    Convert a field visit debrief into structured qualification evidence.

    The output is designed to be re-imported into PRIORITIZE / downstream analysis.
    It records observed salesperson input and does not infer clinical suitability.
    """
    engagement_signal, engagement_status = OUTCOME_SIGNALS.get(
        outcome,
        ("cold", "unverified"),
    )
    value = max(0.0, _number(estimated_value_eur, 0.0))

    company = _text(account.get("company") or account.get("company_name"))
    country = _text(account.get("country"))
    region = _text(account.get("region") or account.get("territory_region"))
    industry = _text(account.get("industry")) or "Medical Aesthetics"

    return {
        "company_name": company,
        "company": company,
        "country": country,
        "region": region,
        "industry": industry,
        "field_visit_completed": True,
        "field_visit_date": visit_date or date.today().isoformat(),
        "field_outcome": outcome,
        "field_needs_summary": _text(needs_summary),
        "field_patient_demand": _text(patient_demand),
        "field_current_technologies": _text(current_technologies),
        "field_decision_process": _text(decision_process),
        "field_investment_timing": _text(investment_timing),
        "field_product_interest": _text(product_interest),
        "field_notes": _text(notes),
        "engagement_signal": engagement_signal,
        "engagement_status": engagement_status,
        "estimated_deal_value_eur": value,
        "estimated_deal_value_usd": value,
        "deal_value_status": "verified" if value > 0 else "unknown",
        "field_next_action": _text(next_action),
        "source_stage": "FIELD_VISIT_FEEDBACK",
        "feedback_basis": (
            "Salesperson-entered field evidence. Verify commercial values and decision details "
            "before using them for forecasting or contracting."
        ),
    }
