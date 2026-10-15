from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from client_reporting import build_funnel_rows, client_report_to_markdown
from mandate_reporting import build_mandate_report
from mandate_workspace import APP_LABELS, stage_url
from workspace_cloud import (
    cloud_settings,
    list_workspaces,
    save_workspace,
    workspace_label,
)
from workspace_dashboard import build_next_action_queue, workspace_counts
from workspace_persistence import is_enabled
from workspace_snapshot import (
    snapshot_filename,
    snapshot_from_json,
    snapshot_to_json,
)


st.set_page_config(
    page_title="Ambrosin Mandate Workspace",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Ambrosin Commercial Mandate Workspace")
st.caption(
    "One operational view for mandate context, pipeline progress, next actions, "
    "active opportunities and workspace persistence."
)

config, workspace_table = cloud_settings(st)
cloud_enabled = is_enabled(config)

selected_cloud_snapshot = {}
cloud_records = []

if cloud_enabled:
    try:
        cloud_records = list_workspaces(
            config,
            workspace_table,
        )
    except Exception as exc:
        st.warning(
            "Cloud workspace could not be reached. "
            f"Portable snapshots remain available. Details: {exc}"
        )

    if cloud_records:
        labels = ["— Select a saved workspace —"] + [
            workspace_label(record)
            for record in cloud_records
        ]
        selected_label = st.selectbox(
            "Saved Mandate Workspace",
            labels,
            help=(
                "Resume a previously saved mandate, pipeline, execution log, "
                "deal sheets and field-visit feedback."
            ),
        )
        if selected_label != labels[0]:
            record = cloud_records[labels.index(selected_label) - 1]
            payload = record.get("payload")
            if isinstance(payload, dict):
                selected_cloud_snapshot = payload
    else:
        st.caption(
            "Cloud persistence is configured, but no saved workspace exists yet."
        )
else:
    st.info(
        "Cloud persistence is optional and currently not configured. "
        "You can still open, inspect and download portable Workspace Snapshots."
    )

uploaded_snapshot = st.file_uploader(
    "Open portable Workspace Snapshot",
    type=["json"],
    help=(
        "A portable ENGAGE snapshot contains the mandate, pipeline, execution updates, "
        "deal sheets and field-visit feedback."
    ),
)

workspace_snapshot = dict(selected_cloud_snapshot)

if uploaded_snapshot is not None:
    try:
        workspace_snapshot = snapshot_from_json(
            uploaded_snapshot.getvalue()
        )
        st.success(
            "Portable Workspace Snapshot loaded. "
            "It overrides the cloud selection for this page."
        )
    except Exception as exc:
        st.error(f"Could not open Workspace Snapshot: {exc}")
        st.stop()

if not workspace_snapshot:
    st.markdown("### Start from an existing ENGAGE workspace")
    st.write(
        "Create or load a pipeline in ENGAGE, save a Workspace Snapshot, then open it here. "
        "When cloud persistence is configured, the same snapshot can be saved and resumed "
        "without relying on the local file."
    )
    st.stop()

mandate = workspace_snapshot.get("mandate", {}) or {}
pipeline = pd.DataFrame(
    workspace_snapshot.get("pipeline", []) or []
)
execution_updates = list(
    workspace_snapshot.get("execution_updates", []) or []
)
deal_sheets = list(
    workspace_snapshot.get("deal_sheets", []) or []
)
field_feedback = list(
    workspace_snapshot.get("field_visit_feedback", []) or []
)

st.divider()
st.subheader("Commercial Mandate")

m1, m2, m3, m4 = st.columns(4)
m1.caption("Client / represented company")
m1.markdown(
    f"**{mandate.get('mandate_client') or 'Not specified'}**"
)
m2.caption("Commercial corridor")
m2.markdown(
    f"**{mandate.get('mandate_corridor') or 'Not specified'}**"
)
m3.caption("Product / solution")
m3.markdown(
    f"**{mandate.get('mandate_product') or 'Not specified'}**"
)
m4.caption("Target market")
m4.markdown(
    f"**{mandate.get('mandate_target_market') or 'Not specified'}**"
)

mandate_name = mandate.get("mandate_name") or "Commercial Mandate"
st.markdown(f"### {mandate_name}")

objective = str(
    mandate.get("mandate_commercial_objective") or ""
).strip()
if objective:
    st.caption("Commercial objective")
    st.write(objective)

counts = workspace_counts(workspace_snapshot)
with st.expander("Workspace records", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pipeline records", counts["pipeline"])
    c2.metric("Execution updates", counts["execution_updates"])
    c3.metric("Deal sheets", counts["deal_sheets"])
    c4.metric("Field feedback", counts["field_visit_feedback"])

report = build_mandate_report(
    pipeline,
    execution_updates=execution_updates,
    deal_sheets=deal_sheets,
)

st.divider()
st.subheader("Mandate Funnel")

f1, f2, f3, f4 = st.columns(4)
f1.metric("Researched", report["total_counterparties"])
f2.metric("Qualified", report["qualified_counterparties"])
f3.metric("Contacted", report["contacted"])
f4.metric("Responses", report["responses"])

f5, f6, f7, f8 = st.columns(4)
f5.metric("Meetings", report["meetings"])
f6.metric("Opportunities", report["active_opportunities"])
f7.metric("Quotations", report["quotations"])
f8.metric("Won", report["won"])

funnel_df = pd.DataFrame(
    build_funnel_rows(report)
)
st.dataframe(
    funnel_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Share of current pipeline": st.column_config.NumberColumn(
            "Share of current pipeline",
            format="%.1f%%",
        ),
    },
)

st.divider()
st.subheader("Next Action Queue")
st.caption(
    "Overdue and due-today actions are surfaced first, followed by upcoming "
    "and unscheduled actions. Opportunity stage and upstream tier influence priority."
)

action_rows = build_next_action_queue(
    execution_updates
)

if action_rows:
    action_df = pd.DataFrame(action_rows)
    status_options = [
        "All",
        "Overdue",
        "Due Today",
        "Upcoming",
        "Unscheduled",
    ]
    selected_status = st.selectbox(
        "Action status",
        status_options,
    )
    if selected_status != "All":
        action_df = action_df[
            action_df["Status"] == selected_status
        ]
    st.dataframe(
        action_df,
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info(
        "No next actions are recorded yet. Add a next action and date in the "
        "ENGAGE Business Development Execution Log."
    )

st.divider()
st.subheader("Commercial Opportunities")

pipeline_values = report.get(
    "pipeline_value_by_currency",
    {},
) or {}

if pipeline_values:
    st.markdown(
        "**Indicative opportunity value:** "
        + " · ".join(
            f"{currency} {value:,.0f}"
            for currency, value in pipeline_values.items()
        )
    )

if deal_sheets:
    deal_columns = [
        "company_name",
        "deal_stage",
        "deal_product",
        "deal_indicative_value",
        "deal_currency",
        "quotation_status",
        "deal_next_step",
        "deal_next_step_date",
        "commercial_risks",
    ]
    deal_df = pd.DataFrame(deal_sheets)
    visible_columns = [
        column
        for column in deal_columns
        if column in deal_df.columns
    ]
    st.dataframe(
        deal_df[visible_columns],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info(
        "No Commercial Deal Sheets are saved in this workspace yet."
    )

st.divider()
st.subheader("Client Reporting")

reporting_period = st.text_input(
    "Reporting period",
    value=date.today().strftime("%B %Y"),
)
client_report = client_report_to_markdown(
    report,
    reporting_period=reporting_period,
)

report_col, snapshot_col = st.columns(2)
with report_col:
    st.download_button(
        "⬇ Client Report — Markdown",
        client_report,
        file_name="ambrosin_client_mandate_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
with snapshot_col:
    st.download_button(
        "⬇ Portable Workspace Snapshot",
        snapshot_to_json(workspace_snapshot),
        file_name=snapshot_filename(workspace_snapshot),
        mime="application/json",
        use_container_width=True,
    )

st.divider()
st.subheader("Workspace Persistence")

if cloud_enabled:
    st.caption(
        "Cloud storage uses Streamlit server-side secrets. "
        "Do not expose the database key in source code or client-side applications."
    )
    if st.button(
        "☁️ Save / Update Workspace in Cloud",
        type="primary",
        use_container_width=True,
    ):
        try:
            workspace_snapshot = save_workspace(
                config,
                workspace_table,
                workspace_snapshot,
            )
            st.success(
                "Mandate Workspace saved. The same workspace can be resumed in a later session."
            )
        except Exception as exc:
            st.error(f"Could not save Workspace: {exc}")
else:
    st.caption(
        "Configure the private Supabase backend to enable cross-session persistence. "
        "Until then, use the portable Workspace Snapshot."
    )

st.warning(
    "Workspace Snapshots and cloud records may contain commercially sensitive information. "
    "Use a private database and apply the confidentiality requirements of each mandate."
)

st.divider()
st.subheader("Commercial Intelligence Modules")

module_cols = st.columns(4)
for column, stage in zip(
    module_cols,
    ["IDENTIFY", "PRIORITIZE", "PARTNER", "ENGAGE"],
):
    with column:
        st.markdown(f"**{stage}**")
        st.caption(APP_LABELS[stage])
        st.link_button(
            f"Open {stage}",
            stage_url(stage, mandate),
            use_container_width=True,
        )
