from __future__ import annotations

from typing import Any, Mapping


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_funnel_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    total = int(report.get("total_counterparties", 0) or 0)
    stages = [
        ("Researched / In Pipeline", total),
        ("Qualified", int(report.get("qualified_counterparties", 0) or 0)),
        ("Contacted", int(report.get("contacted", 0) or 0)),
        ("Responses", int(report.get("responses", 0) or 0)),
        ("Meetings", int(report.get("meetings", 0) or 0)),
        ("Active Opportunities", int(report.get("active_opportunities", 0) or 0)),
        ("Quotations / Proposals", int(report.get("quotations", 0) or 0)),
        ("Won", int(report.get("won", 0) or 0)),
    ]
    return [
        {
            "Stage": stage,
            "Count": count,
            "Share of current pipeline": (
                round(count / total * 100, 1)
                if total > 0
                else 0.0
            ),
        }
        for stage, count in stages
    ]


def client_report_to_markdown(
    report: Mapping[str, Any],
    *,
    reporting_period: str,
    prepared_by: str = "Ambrosin Legal Trade",
) -> str:
    context = report.get("mandate_context", {}) or {}
    client = _clean(context.get("mandate_client"))
    corridor = _clean(context.get("mandate_corridor"))
    product = _clean(context.get("mandate_product"))
    objective = _clean(context.get("mandate_commercial_objective"))
    target_market = _clean(context.get("mandate_target_market"))

    lines = [
        "# Commercial Mandate Report",
        "",
        f"**Prepared by:** {prepared_by}",
        f"**Reporting period:** {_clean(reporting_period) or 'Not specified'}",
        f"**Client / represented company:** {client or 'Not specified'}",
        f"**Mandate:** {_clean(report.get('mandate_summary')) or 'Not specified'}",
        f"**Commercial corridor:** {corridor or 'Not specified'}",
        f"**Target market:** {target_market or 'Not specified'}",
        f"**Product / solution:** {product or 'Not specified'}",
        "",
        "## Executive Summary",
        "",
        (
            f"The current mandate pipeline contains "
            f"{int(report.get('total_counterparties', 0))} counterparties, "
            f"{int(report.get('qualified_counterparties', 0))} qualified counterparties, "
            f"{int(report.get('meetings', 0))} recorded meetings and "
            f"{int(report.get('active_opportunities', 0))} active opportunities."
        ),
    ]

    if objective:
        lines += ["", f"**Commercial objective:** {objective}"]

    lines += ["", "## Mandate Funnel", ""]
    for row in build_funnel_rows(report):
        lines.append(
            f"- {row['Stage']}: {row['Count']} "
            f"({row['Share of current pipeline']:.1f}% of current pipeline)"
        )

    lines += ["", "## Indicative Opportunity Value", ""]
    values = report.get("pipeline_value_by_currency", {}) or {}
    if values:
        for currency, value in values.items():
            lines.append(f"- {currency}: {float(value):,.0f}")
    else:
        lines.append("- No entered opportunity values in the current workflow.")

    lines += ["", "## Priority Opportunities", ""]
    top_deals = report.get("top_deals", []) or []
    if top_deals:
        for item in top_deals:
            amount_value = float(item.get("deal_indicative_value", 0) or 0)
            amount_currency = _clean(item.get("deal_currency"))
            amount = (
                f"{amount_currency} {amount_value:,.0f}"
                if amount_value > 0
                else "value to qualify"
            )
            lines.append(
                f"- {_clean(item.get('company_name')) or 'Unnamed account'} — "
                f"{_clean(item.get('deal_stage')) or 'stage to qualify'} — {amount}"
            )
            next_step = _clean(item.get("deal_next_step"))
            if next_step:
                lines.append(f"  - Next step: {next_step}")
    else:
        lines.append("- No Commercial Deal Sheets recorded yet.")

    lines += ["", "## Next Actions", ""]
    actions = report.get("pending_actions", []) or []
    if actions:
        for item in actions:
            date = _clean(item.get("next_action_date"))
            suffix = f" — {date}" if date else ""
            lines.append(
                f"- {_clean(item.get('company_name')) or 'Unnamed account'}: "
                f"{_clean(item.get('next_action'))}{suffix}"
            )
    else:
        lines.append("- No next actions recorded yet.")

    lines += [
        "",
        "## Reporting Note",
        "",
        (
            "This report reflects the commercial records currently loaded or entered "
            "in the workflow. It is an operational Business Development report, not an "
            "independent market-size study, legal opinion or guarantee of conversion."
        ),
    ]

    return "\n".join(lines)
