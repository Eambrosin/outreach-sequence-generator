from __future__ import annotations

from typing import Any, Mapping

from commercial_mandate import mandate_from_mapping
from trade_feasibility import feasibility_from_mapping


OPPORTUNITY_STAGES = [
    "Research",
    "Contacted",
    "Response Received",
    "Qualification",
    "Meeting Scheduled",
    "Meeting Completed",
    "Active Opportunity",
    "Quotation / Proposal",
    "Negotiation",
    "Won",
    "Lost",
    "On Hold",
]

RESPONSE_STATUSES = [
    "Not Contacted",
    "No Response Yet",
    "Positive Response",
    "Neutral / Needs Follow-Up",
    "Not Now",
    "Not a Fit",
    "Referred Internally",
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    return str(value).strip()


def build_execution_update(
    lead: Mapping[str, Any],
    *,
    opportunity_stage: str,
    response_status: str,
    meeting_outcome: str = "",
    commercial_interest: str = "",
    products_discussed: str = "",
    decision_process: str = "",
    budget_status: str = "",
    timeline: str = "",
    technical_questions: str = "",
    objections: str = "",
    documents_requested: str = "",
    next_action: str = "",
    next_action_date: str = "",
    execution_notes: str = "",
) -> dict[str, Any]:
    update = {
        "schema_version": "1.0",
        "source_stage": "ENGAGE_EXECUTION",
        "company_name": _clean(
            lead.get("company_name", lead.get("company", ""))
        ),
        "contact_name": _clean(lead.get("contact_name", "")),
        "country": _clean(lead.get("country", "")),
        "industry": _clean(lead.get("industry", "")),
        "opportunity_stage": _clean(opportunity_stage),
        "response_status": _clean(response_status),
        "meeting_outcome": _clean(meeting_outcome),
        "commercial_interest": _clean(commercial_interest),
        "products_discussed": _clean(products_discussed),
        "decision_process": _clean(decision_process),
        "budget_status": _clean(budget_status),
        "timeline": _clean(timeline),
        "technical_questions": _clean(technical_questions),
        "objections": _clean(objections),
        "documents_requested": _clean(documents_requested),
        "next_action": _clean(next_action),
        "next_action_date": _clean(next_action_date),
        "execution_notes": _clean(execution_notes),
        "upstream_score": lead.get("score", ""),
        "upstream_tier": _clean(lead.get("tier", "")),
        "upstream_recommended_action": _clean(
            lead.get("recommended_action", "")
        ),
    }
    update.update(mandate_from_mapping(lead))
    update.update(feasibility_from_mapping(lead))
    return update
