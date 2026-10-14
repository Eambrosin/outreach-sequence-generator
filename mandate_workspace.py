from __future__ import annotations

from typing import Any, Mapping

APP_URLS = {
    "IDENTIFY": "https://opportunity-discovery-intelligence-eambrosin.streamlit.app/",
    "PRIORITIZE": "https://lead-qualification-scorer-eambrosin.streamlit.app/",
    "PARTNER": "https://partnership-opportunity-finder-eambrosin.streamlit.app/",
    "ENGAGE": "https://outreach-sequence-generator-eambrosin.streamlit.app/",
}

APP_LABELS = {
    "IDENTIFY": "Market Entry & Opportunity Intelligence",
    "PRIORITIZE": "Counterparty Qualification & Commercial Priority",
    "PARTNER": "Route-to-Market & Partner Intelligence",
    "ENGAGE": "Business Development Execution",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "<na>", "null"}:
        return ""
    return text


def workspace_plan(
    current_stage: str,
    mandate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage = _clean(current_stage).upper()
    if stage not in APP_URLS:
        raise ValueError(f"Unknown Commercial Intelligence stage: {current_stage}")

    payload = dict(mandate or {})
    focus = _clean(payload.get("mandate_counterparty_focus")) or "Buyers"

    if stage == "IDENTIFY":
        if focus == "Partners":
            next_stage = "PARTNER"
            next_action = "Evaluate route-to-market partner readiness"
        elif focus == "Buyers + Partners":
            next_stage = "PRIORITIZE / PARTNER"
            next_action = "Qualify buyers and evaluate route-to-market partners"
        else:
            next_stage = "PRIORITIZE"
            next_action = "Qualify and prioritize buyer / end-customer candidates"
    elif stage == "PRIORITIZE":
        next_stage = "ENGAGE"
        next_action = "Move qualified counterparties into Business Development execution"
    elif stage == "PARTNER":
        next_stage = "ENGAGE"
        next_action = "Move validated partner candidates into partner development and follow-up"
    else:
        next_stage = "REPORT"
        next_action = "Advance opportunities, maintain next actions and report mandate progress"

    summary_parts = [
        _clean(payload.get("mandate_name")),
        _clean(payload.get("mandate_corridor")),
        _clean(payload.get("mandate_product")),
        _clean(payload.get("mandate_target_market")),
    ]

    return {
        "current_stage": stage,
        "current_label": APP_LABELS[stage],
        "next_stage": next_stage,
        "next_action": next_action,
        "mandate_loaded": any(summary_parts),
        "mandate_summary": " · ".join(part for part in summary_parts if part),
        "client": _clean(payload.get("mandate_client")),
        "corridor": _clean(payload.get("mandate_corridor")),
        "product": _clean(payload.get("mandate_product")),
        "target_market": _clean(payload.get("mandate_target_market")),
        "counterparty_focus": focus,
    }


def render_mandate_workspace(st, current_stage: str, mandate: Mapping[str, Any] | None = None):
    plan = workspace_plan(current_stage, mandate)

    with st.container(border=True):
        st.markdown("### Ambrosin Commercial Mandate Workspace")
        st.caption(
            "Market Intelligence → Business Development → Commercial Execution"
        )

        nav_cols = st.columns(4)
        for column, stage in zip(
            nav_cols,
            ["IDENTIFY", "PRIORITIZE", "PARTNER", "ENGAGE"],
        ):
            with column:
                label = (
                    f"● {stage}"
                    if stage == plan["current_stage"]
                    else stage
                )
                st.markdown(f"**{label}**")
                st.caption(APP_LABELS[stage])
                st.link_button(
                    f"Open {stage}",
                    APP_URLS[stage],
                    use_container_width=True,
                )

        if plan["mandate_loaded"]:
            st.markdown("**Active Commercial Mandate**")
            detail_cols = st.columns(4)
            detail_cols[0].caption("Client / represented company")
            detail_cols[0].markdown(f"**{plan['client'] or 'Not specified'}**")
            detail_cols[1].caption("Commercial corridor")
            detail_cols[1].markdown(f"**{plan['corridor'] or 'Not specified'}**")
            detail_cols[2].caption("Product / solution")
            detail_cols[2].markdown(f"**{plan['product'] or 'Not specified'}**")
            detail_cols[3].caption("Counterparty focus")
            detail_cols[3].markdown(f"**{plan['counterparty_focus']}**")
        else:
            st.info(
                "No Commercial Mandate is loaded yet. Create one in IDENTIFY or load "
                "the portable mandate JSON to keep context consistent across modules."
            )

        st.markdown(
            f"**Current stage:** {plan['current_stage']} · {plan['current_label']}"
        )
        st.caption(
            f"Recommended progression: {plan['next_stage']} — {plan['next_action']}."
        )

    return plan
