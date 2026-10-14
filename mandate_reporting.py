from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

import pandas as pd

from commercial_mandate import mandate_from_mapping, mandate_summary


ACTIVE_OPPORTUNITY_STAGES = {
    "Active Opportunity",
    "Quotation / Proposal",
    "Negotiation",
    "Won",
}

MEETING_STAGES = {
    "Meeting Scheduled",
    "Meeting Completed",
    "Active Opportunity",
    "Quotation / Proposal",
    "Negotiation",
    "Won",
}

QUOTATION_STAGES = {
    "Commercial Proposal",
    "Quotation Submitted",
    "Negotiation",
    "Contract / PO Review",
    "Won",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _records(values: Iterable[Mapping[str, Any]] | None) -> list[dict]:
    return [dict(item) for item in (values or [])]


def build_mandate_report(
    pipeline: pd.DataFrame,
    execution_updates: Iterable[Mapping[str, Any]] | None = None,
    deal_sheets: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    pipeline = pipeline.copy() if isinstance(pipeline, pd.DataFrame) else pd.DataFrame()
    executions = _records(execution_updates)
    deals = _records(deal_sheets)

    total_counterparties = int(len(pipeline))

    high_priority = 0
    if not pipeline.empty:
        if "tier" in pipeline.columns:
            high_priority = int(
                pipeline["tier"].fillna("").astype(str).str.upper().eq("A").sum()
            )
        elif "priority" in pipeline.columns:
            high_priority = int(
                pipeline["priority"].fillna("").astype(str).str.lower().eq("high").sum()
            )

    qualified = 0
    if not pipeline.empty and "qualification_status" in pipeline.columns:
        statuses = pipeline["qualification_status"].fillna("").astype(str)
        qualified = int(
            statuses.isin(
                ["Commercially Qualified", "Field Qualified"]
            ).sum()
        )
    elif not pipeline.empty and "qualification_readiness_status" in pipeline.columns:
        qualified = int(
            pipeline["qualification_readiness_status"]
            .fillna("")
            .astype(str)
            .eq("Ready for Qualification")
            .sum()
        )

    contacted = sum(
        1
        for item in executions
        if _clean(item.get("opportunity_stage")) != "Research"
        or _clean(item.get("response_status"))
        not in {"", "Not Contacted"}
    )

    responses = sum(
        1
        for item in executions
        if _clean(item.get("response_status"))
        not in {"", "Not Contacted", "No Response Yet"}
    )

    meetings = sum(
        1
        for item in executions
        if _clean(item.get("opportunity_stage")) in MEETING_STAGES
        or bool(_clean(item.get("meeting_outcome")))
    )

    active_opportunities = sum(
        1
        for item in executions
        if _clean(item.get("opportunity_stage")) in ACTIVE_OPPORTUNITY_STAGES
    )

    quotations = sum(
        1
        for item in deals
        if _clean(item.get("deal_stage")) in QUOTATION_STAGES
        or bool(_clean(item.get("quotation_status")))
    )

    won = max(
        sum(
            1
            for item in executions
            if _clean(item.get("opportunity_stage")) == "Won"
        ),
        sum(
            1
            for item in deals
            if _clean(item.get("deal_stage")) == "Won"
        ),
    )

    values_by_currency: dict[str, float] = defaultdict(float)
    for item in deals:
        value = _float(item.get("deal_indicative_value"))
        if value <= 0:
            continue
        currency = _clean(item.get("deal_currency")) or "Unspecified"
        values_by_currency[currency] += value

    pending_actions = [
        {
            "company_name": _clean(item.get("company_name")),
            "next_action": _clean(item.get("next_action")),
            "next_action_date": _clean(item.get("next_action_date")),
            "opportunity_stage": _clean(item.get("opportunity_stage")),
        }
        for item in executions
        if _clean(item.get("next_action"))
    ]

    top_deals = sorted(
        [
            {
                "company_name": _clean(item.get("company_name")),
                "deal_stage": _clean(item.get("deal_stage")),
                "deal_indicative_value": _float(
                    item.get("deal_indicative_value")
                ),
                "deal_currency": _clean(item.get("deal_currency")),
                "deal_next_step": _clean(item.get("deal_next_step")),
            }
            for item in deals
        ],
        key=lambda item: item["deal_indicative_value"],
        reverse=True,
    )

    mandate_context = {}
    if not pipeline.empty:
        mandate_context = pipeline.iloc[0].to_dict()
    elif executions:
        mandate_context = executions[0]
    elif deals:
        mandate_context = deals[0]

    mandate_payload = mandate_from_mapping(mandate_context)

    return {
        "mandate_summary": mandate_summary(mandate_context),
        "mandate_context": mandate_payload,
        "total_counterparties": total_counterparties,
        "qualified_counterparties": qualified,
        "high_priority_counterparties": high_priority,
        "contacted": contacted,
        "responses": responses,
        "meetings": meetings,
        "active_opportunities": active_opportunities,
        "quotations": quotations,
        "won": won,
        "pipeline_value_by_currency": dict(values_by_currency),
        "pending_actions": pending_actions,
        "top_deals": top_deals[:5],
    }


def report_to_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Commercial Mandate Report",
        "",
        f"**Mandate:** {_clean(report.get('mandate_summary')) or 'Not specified'}",
        "",
        "## Commercial activity",
        "",
        f"- Counterparties in current pipeline: {int(report.get('total_counterparties', 0))}",
        f"- Qualified counterparties: {int(report.get('qualified_counterparties', 0))}",
        f"- High-priority counterparties: {int(report.get('high_priority_counterparties', 0))}",
        f"- Contacted: {int(report.get('contacted', 0))}",
        f"- Responses: {int(report.get('responses', 0))}",
        f"- Meetings: {int(report.get('meetings', 0))}",
        f"- Active opportunities: {int(report.get('active_opportunities', 0))}",
        f"- Quotations / proposals: {int(report.get('quotations', 0))}",
        f"- Won: {int(report.get('won', 0))}",
        "",
        "## Indicative pipeline",
        "",
    ]

    values = report.get("pipeline_value_by_currency", {}) or {}
    if values:
        for currency, value in values.items():
            lines.append(f"- {currency}: {float(value):,.0f}")
    else:
        lines.append("- No verified / entered deal values yet.")

    lines += ["", "## Top opportunities", ""]
    top_deals = report.get("top_deals", []) or []
    if top_deals:
        for item in top_deals:
            value = float(item.get("deal_indicative_value", 0) or 0)
            currency = _clean(item.get("deal_currency"))
            amount = f"{currency} {value:,.0f}" if value > 0 else "value to qualify"
            lines.append(
                f"- {_clean(item.get('company_name')) or 'Unnamed account'} — "
                f"{_clean(item.get('deal_stage')) or 'stage to qualify'} — {amount}"
            )
    else:
        lines.append("- No deal sheets recorded yet.")

    lines += ["", "## Next actions", ""]
    actions = report.get("pending_actions", []) or []
    if actions:
        for item in actions:
            date = _clean(item.get("next_action_date"))
            suffix = f" ({date})" if date else ""
            lines.append(
                f"- {_clean(item.get('company_name')) or 'Unnamed account'}: "
                f"{_clean(item.get('next_action'))}{suffix}"
            )
    else:
        lines.append("- No next actions recorded yet.")

    lines += [
        "",
        "> Metrics reflect the records currently loaded or entered in the workflow. "
        "They are operational reporting indicators, not market-size or conversion-rate claims.",
    ]

    return "\n".join(lines)
