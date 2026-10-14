import html
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from field_planner import build_field_day_plan
from visit_feedback import OUTCOME_SIGNALS, build_visit_feedback
from commercial_mandate import (
    apply_mandate_fields,
    has_mandate_context,
    mandate_from_json,
    mandate_summary,
)
from bd_execution import (
    OPPORTUNITY_STAGES,
    RESPONSE_STATUSES,
    build_execution_update,
)
from commercial_deal import (
    DEAL_STAGES,
    build_commercial_deal_sheet,
)
from mandate_reporting import (
    build_mandate_report,
    report_to_markdown,
)
from outreach_generator import (
    COUNTRY_PROFILE,
    DEFAULT_PROFILE,
    build_outreach_strategy,
    generate_local_sequence,
    generate_sequence,
    normalize_lead,
)


st.set_page_config(
    page_title="Business Development Execution & Outreach",
    page_icon="📨",
    layout="wide",
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def format_money(value):
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return str(value)


def optional(value, fallback="Not provided"):
    if value is None:
        return fallback

    try:
        if pd.isna(value):
            return fallback
    except Exception:
        pass

    text = str(value).strip()

    return text or fallback


def score_text(value):
    try:
        if value is None or pd.isna(value):
            return "N/A"

        return f"{float(value):.1f}"

    except Exception:
        return "N/A"


def proposal_age_text(value):
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"

        return f"{int(float(value))} days"

    except Exception:
        return "N/A"


def safe_filename(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def get_profile(country):
    return COUNTRY_PROFILE.get(
        str(country).strip(),
        DEFAULT_PROFILE,
    )


def priority_rank(priority):
    return {
        "High": 3,
        "Medium": 2,
        "Low": 1,
    }.get(
        priority,
        0,
    )


def render_card(
    title,
    content,
    icon="📌",
):
    safe_content = html.escape(
        str(
            content
            or "Not provided"
        )
    )

    st.markdown(
        f"#### {icon} {title}"
    )

    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(128,128,128,.25);
            border-radius:14px;
            padding:16px;
            margin-bottom:12px;
            white-space:pre-wrap;
            line-height:1.55;
        ">{safe_content}</div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(
    label,
    value,
    caption="",
):
    with st.container(border=True):
        st.caption(label)
        st.markdown(
            f"**{optional(value, 'Not provided')}**"
        )
        if caption:
            st.caption(caption)


def split_pipe_values(value):
    return [
        item.strip()
        for item in str(value or "").split(" | ")
        if item.strip()
    ]


def render_list_card(
    title,
    value,
    icon="📌",
):
    items = split_pipe_values(value)

    st.markdown(
        f"#### {icon} {title}"
    )

    with st.container(border=True):
        if not items:
            st.write("Not provided")
        else:
            for item in items:
                st.markdown(f"- {item}")


def sequence_to_text(
    company,
    sequence,
):
    lines = [
        f"Adaptive Outreach Sequence — {company}",
        "",
    ]

    for data in sequence.values():

        lines.append(
            data.get(
                "label",
                "Outreach Touch",
            )
        )

        lines.append(
            f"Timing: "
            f"{data.get('timing', '')}"
        )

        lines.append(
            f"Channel: "
            f"{data.get('channel', '')}"
        )

        if data.get(
            "subject"
        ):
            lines.append(
                f"Subject: "
                f"{data['subject']}"
            )

        lines += [
            "",
            data.get(
                "message",
                "",
            ),
            "",
            "-" * 60,
            "",
        ]

    return "\n".join(
        lines
    )


def validate_pipeline(
    dataframe,
):
    groups = {

        "company": [
            "company",
            "company_name",
        ],

        "country": [
            "country",
        ],

        "industry": [
            "industry",
        ],

        "deal value": [
            "deal_value_usd",
            "estimated_deal_value_usd",
        ],
    }

    missing = []

    for label, alternatives in groups.items():

        if not any(
            column in dataframe.columns
            for column in alternatives
        ):

            missing.append(
                f"{label} "
                f"({' or '.join(alternatives)})"
            )

    return missing


def stakeholder_function(
    industry,
):
    mapping = {

        "Agribusiness": (
            "Commercial, Procurement, International Trade "
            "or Business Development leadership"
        ),

        "Logistics & Trade": (
            "Commercial, International Trade, Partnerships "
            "or Business Development leadership"
        ),

        "Fintech": (
            "Partnerships, Strategy, Growth "
            "or Business Development leadership"
        ),

        "Renewable Energy": (
            "Partnerships, Strategy, Commercial "
            "or Business Development leadership"
        ),

        "Real Estate": (
            "Investment, Partnerships, Asset Management "
            "or Business Development leadership"
        ),

        "Government / Public Sector": (
            "Institutional Relations, Procurement, Partnerships "
            "or Program leadership"
        ),

        "Medical Aesthetics": (
            "Owner/Founder, Medical Director, Aesthetic Physician, Dermatologist, "
            "Clinic/Practice Manager or qualified aesthetic professional, depending on product eligibility"
        ),
    }

    return mapping.get(
        industry,
        (
            "Commercial, Partnerships, Strategy "
            "or Business Development leadership"
        ),
    )


def decision_risk(
    lead,
    priority,
):
    days = lead.get(
        "proposal_sent_days_ago"
    )

    if days is None:

        return (
            "No proposal-age signal is available. "
            "Validate risk through engagement and qualification."
        )

    try:

        days = int(
            float(
                days
            )
        )

    except Exception:

        return (
            "Proposal-age risk could not be calculated."
        )

    if (
        days >= 10
        and priority == "High"
    ):

        return (
            "High attention required: a high-priority opportunity "
            "has an extended post-proposal silence period."
        )

    if days >= 10:

        return (
            "Elevated follow-up risk: the proposal has been "
            "waiting 10 or more days."
        )

    if days >= 5:

        return (
            "Moderate follow-up risk: momentum should be reinforced "
            "with a clear next step."
        )

    return (
        "Low timing risk based on proposal age. "
        "Keep the follow-up consultative."
    )


def touch_channel(
    primary_channel,
    touch_number,
):

    if primary_channel == "Email+WhatsApp":

        if touch_number == 1:
            return "Email"

        return "WhatsApp"

    return primary_channel


# ---------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------

st.title(
    "📨 Business Development Execution & Outreach"
)

st.caption(
    "Turn mandate and qualification context into multilingual outreach, "
    "qualified dialogue, follow-up and active commercial opportunities."
)


# ---------------------------------------------------------------------
# AI STATUS
# ---------------------------------------------------------------------

ai_enabled = bool(
    os.environ.get(
        "ANTHROPIC_API_KEY"
    )
)


# ---------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------

with st.sidebar:

    st.header(
        "Outreach Intelligence"
    )

    if ai_enabled:

        st.success(
            "AI-assisted generation enabled"
        )

    else:

        st.info(
            "Deterministic local generation enabled"
        )

    st.caption(
        "The strategy engine determines priority, cadence and channel logic. "
        "AI, when configured, generates prospect-facing copy."
    )

    if ai_enabled:
        st.caption(
            "When AI generation is used, the selected account context is sent to Anthropic. "
            "Avoid uploading sensitive personal or confidential information."
        )

    st.divider()

    st.markdown(
        "**Accepted pipeline formats**"
    )

    st.caption(
        "Standard outreach CSVs and exports from "
        "Counterparty Qualification & Commercial Priority are supported."
    )

    with st.expander(
        "Supported fields"
    ):

        st.code(
            """Standard fields
contact_name
company
country
industry
deal_type
deal_value_usd
proposal_sent_days_ago
your_name

Commercial Intelligence fields
company_name
region
company_size
estimated_deal_value_usd
engagement_signal
score
tier
recommended_action
score_rationale
market_profile_id
source_stage
linkedin_url
contact_headline
outreach_angle
professional_setting
territory_profile_id
vendor_profile_id
territory_region
territory_province
territory_city
territory_cluster_id
territory_status
account_opportunity_score
contact_readiness_score
contact_status
visit_priority
visit_priority_score
visit_priority_basis
product_fit_family
product_fit_score
product_fit_status
product_fit_basis
planning_opportunity_value_eur
planning_value_status
planning_value_basis
field_visit_objective
field_opening_questions
field_next_best_action
observed_technology_axes
technology_validation_questions
account_website
website_evidence_status
public_phone
public_email
public_address
contact_channel_status
enrichment_status
account_data_completeness
decision_maker_name
decision_maker_headline
decision_maker_linkedin
decision_maker_confidence

Evidence-aware handoff v2
schema_version
source_stage
account_type
commercial_track
qualification_readiness_score
qualification_readiness_status
qualification_readiness_evidence
sales_motion
buyer_access_status
commercial_hypothesis
commercial_angle
next_best_action
qualification_questions
sales_evidence_gaps
commercial_risk_flags
sales_intelligence_basis
contact_relevance_score
contact_confidence
professional_role_signal
location_match_evidence
contact_match_rationale
contact_outreach_angle
public_contact_form
primary_evidence_url
enrichment_evidence_url""",
            language="text",
        )


# ---------------------------------------------------------------------
# LOAD PIPELINE
# ---------------------------------------------------------------------

uploaded = st.file_uploader(
    "Upload Pipeline CSV",
    type=[
        "csv"
    ],
)


if uploaded is not None:

    raw_df = pd.read_csv(
        uploaded
    )

    source_name = (
        uploaded.name
    )

else:

    sample_path = Path(
        "data/pipeline.csv"
    )

    if not sample_path.exists():

        st.info(
            "Upload a pipeline CSV to start. "
            "No default data/pipeline.csv was found."
        )

        st.stop()

    raw_df = pd.read_csv(
        sample_path
    )

    source_name = str(
        sample_path
    )


if raw_df.empty:

    st.warning(
        "The pipeline is empty."
    )

    st.stop()


missing = validate_pipeline(
    raw_df
)


if missing:

    st.error(
        "The pipeline is missing required information: "
        + ", ".join(
            missing
        )
    )

    st.stop()


# ---------------------------------------------------------------------
# NORMALIZE PIPELINE
# ---------------------------------------------------------------------

normalized_leads = [

    normalize_lead(
        row.to_dict()
    )

    for _, row
    in raw_df.iterrows()
]


dashboard_rows = []


for lead in normalized_leads:

    profile = get_profile(
        lead[
            "country"
        ]
    )

    strategy = build_outreach_strategy(
        lead,
        profile,
    )

    dashboard_rows.append(
        {

            **lead,

            "mode": (
                strategy[
                    "mode"
                ]
            ),

            "priority": (
                strategy[
                    "priority"
                ]
            ),

            "intensity": (
                strategy[
                    "intensity"
                ]
            ),

            "recommended_channel": (
                strategy[
                    "primary_channel"
                ]
            ),

            "language": (
                strategy[
                    "language"
                ]
            ),

            "cadence": (
                " → ".join(
                    f"Day +{day}"
                    for day
                    in strategy[
                        "cadence_days"
                    ]
                )
            ),

            "commercial_objective": (
                strategy[
                    "commercial_objective"
                ]
            ),

            "_priority_rank": (
                priority_rank(
                    strategy[
                        "priority"
                    ]
                )
            ),
        }
    )


df = pd.DataFrame(
    dashboard_rows
)

if not df.empty and has_mandate_context(df.iloc[0].to_dict()):
    st.info(
        "**Commercial Mandate:** "
        + mandate_summary(df.iloc[0].to_dict())
        + "  \\nOutreach preserves the mandate context and qualification gaps from upstream."
    )


# ---------------------------------------------------------------------
# DETECT PIPELINE MODE
# ---------------------------------------------------------------------

commercial_intelligence_accounts = int(
    df[
        "commercial_intelligence_mode"
    ].sum()
)


if (
    commercial_intelligence_accounts
    == len(
        df
    )
):

    pipeline_mode = (
        "Commercial Intelligence Mode"
    )

elif (
    commercial_intelligence_accounts
    == 0
):

    pipeline_mode = (
        "Standard Outreach Mode"
    )

else:

    pipeline_mode = (
        "Mixed Pipeline Mode"
    )


st.info(
    f"**Pipeline mode:** {pipeline_mode}  |  "
    f"**Source:** {source_name}"
)


# ---------------------------------------------------------------------
# EXECUTIVE SUMMARY
# ---------------------------------------------------------------------

st.subheader(
    "📊 Executive Summary"
)


total_pipeline_value = float(
    df[
        "deal_value_usd"
    ].sum()
)


high_priority_accounts = int(
    (
        df[
            "priority"
        ]
        == "High"
    ).sum()
)


country_count = int(
    df[
        "country"
    ]
    .replace(
        "",
        pd.NA,
    )
    .dropna()
    .nunique()
)


summary_1, summary_2, summary_3, summary_4, summary_5 = st.columns(
    5
)


summary_1.metric(
    "Total Accounts",
    len(
        df
    ),
)


summary_2.metric(
    "Pipeline Value",
    format_money(
        total_pipeline_value
    ),
)


summary_3.metric(
    "High Priority",
    high_priority_accounts,
)


summary_4.metric(
    "CI Accounts",
    commercial_intelligence_accounts,
)


summary_5.metric(
    "Countries",
    country_count,
)

territory_df = df[
    df.get("territory_profile_id", pd.Series([""] * len(df)))
    .fillna("")
    .astype(str)
    .str.strip()
    != ""
].copy()

if not territory_df.empty:
    st.divider()
    st.subheader("🗺️ Territory Execution Dashboard")
    st.caption(
        "Operational view of accounts that arrived with Territory Intelligence metadata."
    )

    te1, te2, te3, te4, te5 = st.columns(5)
    te1.metric("Territory Accounts", len(territory_df))
    te2.metric(
        "Ready for Outreach",
        int((territory_df.get("contact_status", "") == "Ready for Outreach").sum())
        if "contact_status" in territory_df.columns else 0,
    )
    te3.metric(
        "Ready for Field Visit",
        int((territory_df.get("contact_status", "") == "Ready for Field Visit").sum())
        if "contact_status" in territory_df.columns else 0,
    )
    te4.metric(
        "Qualification Outreach",
        int(
            (
                territory_df.get(
                    "sales_motion",
                    pd.Series([""] * len(territory_df)),
                )
                == "Ready for Qualification Outreach"
            ).sum()
        )
        if "sales_motion" in territory_df.columns else 0,
    )
    te5.metric(
        "Eligibility Validation",
        int((territory_df.get("territory_status", "") == "Eligibility Validation").sum())
        if "territory_status" in territory_df.columns else 0,
    )

    if "territory_region" in territory_df.columns:
        territory_exec = (
            territory_df.groupby("territory_region", dropna=False)
            .agg(
                accounts=("company", "count"),
                high_priority=("priority", lambda v: int((v == "High").sum())),
                avg_opportunity=("account_opportunity_score", "mean"),
                avg_contact_readiness=("contact_readiness_score", "mean"),
            )
            .reset_index()
        )
        territory_exec["avg_opportunity"] = territory_exec["avg_opportunity"].round(1)
        territory_exec["avg_contact_readiness"] = territory_exec["avg_contact_readiness"].round(1)
        st.dataframe(
            territory_exec,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("🚗 Field Day Planner", expanded=False):
        st.caption(
            "Builds a ranked visit shortlist inside one geographic cluster. "
            "It does not claim to optimize driving routes or travel time."
        )

        field_regions = sorted(
            value
            for value in territory_df.get(
                "territory_region",
                pd.Series(dtype=str),
            ).dropna().astype(str).unique().tolist()
            if value.strip()
        )

        field_region = st.selectbox(
            "Field region",
            options=["All"] + field_regions,
            key="field_day_region",
        )

        province_source = territory_df
        if field_region != "All" and "territory_region" in territory_df.columns:
            province_source = territory_df[
                territory_df["territory_region"].astype(str) == field_region
            ]

        field_provinces = sorted(
            value
            for value in province_source.get(
                "territory_province",
                pd.Series(dtype=str),
            ).dropna().astype(str).unique().tolist()
            if value.strip()
        )

        field_province = st.selectbox(
            "Field province",
            options=["All"] + field_provinces,
            key="field_day_province",
        )

        city_source = province_source
        if field_province != "All" and "territory_province" in province_source.columns:
            city_source = province_source[
                province_source["territory_province"].astype(str) == field_province
            ]

        field_cities = sorted(
            value
            for value in city_source.get(
                "territory_city",
                pd.Series(dtype=str),
            ).dropna().astype(str).unique().tolist()
            if value.strip()
        )

        field_city = st.selectbox(
            "Field city / cluster",
            options=["All"] + field_cities,
            key="field_day_city",
        )

        default_visits = (
            7
            if field_province == "Milano" or field_city == "Milano"
            else 5
        )
        field_max_accounts = st.slider(
            "Maximum visits",
            min_value=2,
            max_value=8,
            value=default_visits,
            key="field_day_max_accounts",
            help=(
                "For dense Milano days, 6–7 qualified visits can be a realistic planning target. "
                "Outside Milano, reduce the count as distance and travel time increase."
            ),
        )

        field_plan = build_field_day_plan(
            territory_df,
            region="" if field_region == "All" else field_region,
            province="" if field_province == "All" else field_province,
            city="" if field_city == "All" else field_city,
            max_accounts=field_max_accounts,
        )

        if field_plan.empty:
            st.info(
                "No territory accounts match the selected field-day filters."
            )
        else:
            st.dataframe(
                field_plan,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "linkedin_url": st.column_config.LinkColumn("LinkedIn"),
                },
            )
            st.download_button(
                "⬇ Download Field Day Plan",
                field_plan.to_csv(index=False).encode("utf-8"),
                file_name="territory_field_day_plan.csv",
                mime="text/csv",
            )



# ---------------------------------------------------------------------
# FIELD VISIT DEBRIEF / LEARNING LOOP
# ---------------------------------------------------------------------

if not territory_df.empty:
    st.divider()
    st.subheader("📝 Field Visit Debrief & Learning Loop")
    st.caption(
        "Capture what was actually learned in the meeting or site visit, convert it into "
        "structured qualification evidence, and export it for re-scoring in PRIORITIZE."
    )

    feedback_account_names = sorted(
        territory_df["company"].dropna().astype(str).unique().tolist()
    )
    feedback_company = st.selectbox(
        "Account visited",
        feedback_account_names,
        key="field_feedback_company",
    )
    feedback_account = (
        territory_df[territory_df["company"].astype(str) == feedback_company]
        .iloc[0]
        .to_dict()
    )

    with st.form("field_visit_debrief_form"):
        fb1, fb2 = st.columns(2)
        with fb1:
            field_outcome = st.selectbox(
                "Visit outcome",
                list(OUTCOME_SIGNALS.keys()),
            )
            product_interest = st.text_input(
                "Product / solution interest",
                value=str(feedback_account.get("product_fit_family", "") or ""),
                help="Observed interest after the conversation; do not use this field as a clinical recommendation.",
            )
            estimated_value_eur = st.number_input(
                "Qualified opportunity value (€)",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                help="Enter only when a realistic commercial scope was discussed or otherwise verified.",
            )
            investment_timing = st.text_input(
                "Investment timing",
                placeholder="e.g. Q1 2027 / 3–6 months / exploratory",
            )
        with fb2:
            current_technologies = st.text_area(
                "Current technologies / providers",
                height=90,
            )
            patient_demand = st.text_area(
                "Operational demand / unmet needs",
                height=90,
            )
            decision_process = st.text_area(
                "Decision process / people involved",
                height=90,
            )

        needs_summary = st.text_area(
            "What did the clinic actually need?",
            height=100,
            help="Summarize the business problem in the clinic's own terms where possible.",
        )
        next_action = st.text_input(
            "Agreed next action",
            placeholder="e.g. schedule demo, send ROI case, follow up with medical director",
        )
        field_notes = st.text_area(
            "Additional field notes",
            height=90,
        )

        save_feedback = st.form_submit_button(
            "Save Visit Debrief",
            use_container_width=True,
        )

    if save_feedback:
        feedback_record = build_visit_feedback(
            feedback_account,
            outcome=field_outcome,
            needs_summary=needs_summary,
            patient_demand=patient_demand,
            current_technologies=current_technologies,
            decision_process=decision_process,
            investment_timing=investment_timing,
            product_interest=product_interest,
            estimated_value_eur=estimated_value_eur,
            next_action=next_action,
            notes=field_notes,
        )
        feedback_records = st.session_state.get("field_visit_feedback_records", [])
        feedback_records.append(feedback_record)
        st.session_state.field_visit_feedback_records = feedback_records
        st.success(
            "Visit evidence saved. The record can now be exported and re-scored in PRIORITIZE."
        )

    feedback_records = st.session_state.get("field_visit_feedback_records", [])
    if feedback_records:
        feedback_df = pd.DataFrame(feedback_records)
        st.dataframe(
            feedback_df,
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "⬇ Download Field Visit Feedback",
            feedback_df.to_csv(index=False).encode("utf-8"),
            file_name="field_visit_feedback.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ---------------------------------------------------------------------
# EXECUTIVE OUTREACH DASHBOARD
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "👔 Executive Business Development Dashboard"
)


st.caption(
    "Prioritize commercial attention using mandate context, qualification evidence, "
    "engagement signals, opportunity stage and next-action discipline."
)


sort_df = df.copy()


sort_df[
    "_score_sort"
] = pd.to_numeric(
    sort_df[
        "score"
    ],
    errors="coerce",
).fillna(
    -1
)


sort_df = sort_df.sort_values(

    [
        "_priority_rank",
        "_score_sort",
        "deal_value_usd",
    ],

    ascending=[
        False,
        False,
        False,
    ],
)


top_priority = (
    sort_df.iloc[
        0
    ]
)


proposal_days_numeric = pd.to_numeric(
    df[
        "proposal_sent_days_ago"
    ],
    errors="coerce",
)


revenue_at_risk = float(

    df.loc[
        proposal_days_numeric
        >= 7,
        "deal_value_usd",
    ].sum()

)


if proposal_days_numeric.notna().any():

    avg_days_waiting = float(
        proposal_days_numeric
        .dropna()
        .mean()
    )

else:

    avg_days_waiting = None


exec_1, exec_2, exec_3, exec_4 = st.columns(
    4
)


exec_1.metric(
    "Top Outreach Priority",
    top_priority[
        "company"
    ],
)


exec_2.metric(
    "Revenue At Risk",
    format_money(
        revenue_at_risk
    ),
)


exec_3.metric(
    "Avg. Proposal Age",
    (
        f"{avg_days_waiting:.1f} days"
        if avg_days_waiting
        is not None
        else "N/A"
    ),
)


exec_4.metric(
    "Primary Cadence",
    top_priority[
        "cadence"
    ],
)


# ---------------------------------------------------------------------
# PRIORITY RANKING
# ---------------------------------------------------------------------

st.markdown(
    "#### 📈 Adaptive Priority Ranking"
)


priority_table = sort_df[
    [
        "company",
        "country",
        "industry",
        "deal_value_usd",
        "score",
        "tier",
        "engagement_signal",
        "priority",
        "intensity",
        "recommended_channel",
        "cadence",
        "recommended_action",
    ]
].copy()


priority_table.columns = [
    "Company",
    "Country",
    "Industry",
    "Deal Value USD",
    "Score",
    "Tier",
    "Engagement",
    "Priority",
    "Intensity",
    "Channel",
    "Cadence",
    "Recommended Action",
]


st.dataframe(
    priority_table,
    width="stretch",
    hide_index=True,
)


st.download_button(

    "⬇ Download Adaptive Priority CSV",

    priority_table.to_csv(
        index=False
    ).encode(
        "utf-8"
    ),

    file_name=(
        "adaptive_outreach_priority.csv"
    ),

    mime=(
        "text/csv"
    ),
)


# ---------------------------------------------------------------------
# CHANNEL MIX
# ---------------------------------------------------------------------

st.markdown(
    "#### 📨 Recommended Channel Mix"
)


channel_mix = (

    df[
        "recommended_channel"
    ]

    .value_counts()

    .rename_axis(
        "Channel"
    )

    .reset_index(
        name="Accounts"
    )
)


st.dataframe(
    channel_mix,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# PIPELINE OVERVIEW
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "🎯 Pipeline Overview"
)


overview_columns = [

    "company",

    "country",

    "region",

    "industry",

    "company_size",

    "deal_value_usd",

    "proposal_sent_days_ago",

    "engagement_signal",

    "score",

    "tier",

    "priority",

    "territory_region",

    "territory_province",

    "territory_city",

    "enrichment_status",

    "account_data_completeness",

    "territory_status",

    "contact_status",

    "qualification_readiness_status",

    "sales_motion",

    "buyer_access_status",

    "mode",
]


st.dataframe(

    df[
        overview_columns
    ],

    width="stretch",

    hide_index=True,
)


# ---------------------------------------------------------------------
# ACCOUNT WORKSPACE
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "🧩 Account & Business Development Workspace"
)


selected_company = st.selectbox(

    "Select an account",

    df[
        "company"
    ].tolist(),
)


selected_row = df[
    df[
        "company"
    ]
    == selected_company
].iloc[
    0
]


# Normalize again so pandas NaN does not alter strategy logic.
lead = normalize_lead(
    selected_row.to_dict()
)


profile = get_profile(
    lead[
        "country"
    ]
)


strategy = build_outreach_strategy(
    lead,
    profile,
)


profile_col_1, profile_col_2, profile_col_3 = st.columns(
    3
)


# ---------------------------------------------------------------------
# ACCOUNT PROFILE
# ---------------------------------------------------------------------

with profile_col_1:

    st.markdown(
        "#### 🏢 Account Profile"
    )

    st.write(
        f"**Company:** "
        f"{lead['company']}"
    )

    st.write(
        f"**Contact:** "
        f"{optional(lead['contact_name'])}"
    )

    st.write(
        f"**Country:** "
        f"{optional(lead['country'])}"
    )

    st.write(
        f"**Region:** "
        f"{optional(lead['region'])}"
    )

    st.write(
        f"**Industry:** "
        f"{optional(lead['industry'])}"
    )

    st.write(
        f"**Company Size:** "
        f"{optional(lead['company_size'])}"
    )

    if lead.get("contact_headline"):
        st.write(
            f"**Contact Headline:** "
            f"{lead['contact_headline']}"
        )

    if lead.get("linkedin_url"):
        st.markdown(
            f"**Public LinkedIn:** [{lead['linkedin_url']}]({lead['linkedin_url']})"
        )

    if lead.get("market_profile_id"):
        st.write(
            f"**Market Profile:** "
            f"{lead['market_profile_id']}"
        )

    if lead.get("territory_profile_id"):
        st.write(
            f"**Territory:** "
            f"{lead.get('territory_region', '')} · "
            f"{lead.get('territory_province', '')} · "
            f"{lead.get('territory_city', '') or 'city to verify'}"
        )

    if lead.get("territory_status"):
        st.write(
            f"**Territory Status:** "
            f"{lead['territory_status']}"
        )

    if lead.get("contact_status"):
        st.write(
            f"**Contact Status:** "
            f"{lead['contact_status']}"
        )

    if lead.get("enrichment_status"):
        st.write(
            f"**Account Enrichment:** "
            f"{lead['enrichment_status']}"
        )

    if lead.get("account_data_completeness"):
        st.write(
            f"**Data Completeness:** "
            f"{lead['account_data_completeness']:.0f}%"
        )

    if lead.get("account_website"):
        st.markdown(
            f"**Account Website:** [{lead['account_website']}]({lead['account_website']})"
        )

    if lead.get("public_address"):
        st.write(
            f"**Public Address:** "
            f"{lead['public_address']}"
        )

    if lead.get("public_phone"):
        st.write(
            f"**Public Phone:** "
            f"{lead['public_phone']}"
        )

    if lead.get("public_email"):
        st.write(
            f"**Public Email:** "
            f"{lead['public_email']}"
        )

    if lead.get("public_contact_form"):
        st.write(
            "**Public Contact Form:** Observed on official website"
        )

    if lead.get("professional_role_signal"):
        st.write(
            f"**Observed Professional Role:** "
            f"{lead['professional_role_signal']}"
        )

    if lead.get("location_match_evidence"):
        st.write(
            f"**Contact Location Match:** "
            f"{lead['location_match_evidence']}"
        )

    if lead.get("decision_maker_name"):
        st.write(
            f"**Decision-Maker Candidate:** "
            f"{lead['decision_maker_name']}"
        )
        if lead.get("decision_maker_headline"):
            st.caption(
                lead["decision_maker_headline"]
            )
        if lead.get("decision_maker_linkedin"):
            st.markdown(
                f"**Decision-Maker LinkedIn:** [{lead['decision_maker_linkedin']}]({lead['decision_maker_linkedin']})"
            )


# ---------------------------------------------------------------------
# COMMERCIAL CONTEXT
# ---------------------------------------------------------------------

with profile_col_2:

    st.markdown(
        "#### 💰 Commercial Context"
    )

    st.write(
        f"**Deal Type:** "
        f"{lead['deal_type']}"
    )

    st.write(
        f"**Deal Value:** "
        f"{format_money(lead['deal_value_usd'])}"
    )

    st.write(
        f"**Stage:** "
        f"{strategy['stage'].replace('_', ' ').title()}"
    )

    st.write(
        f"**Proposal Age:** "
        f"{proposal_age_text(lead['proposal_sent_days_ago'])}"
    )

    st.write(
        f"**Score:** "
        f"{score_text(lead['score'])}"
    )

    st.write(
        f"**Tier:** "
        f"{optional(lead['tier'], 'N/A')}"
    )

    if lead.get("account_opportunity_score"):
        st.write(
            f"**Account Opportunity:** "
            f"{lead['account_opportunity_score']:.1f}"
        )

    if lead.get("contact_readiness_score"):
        st.write(
            f"**Contact Readiness:** "
            f"{lead['contact_readiness_score']:.1f}"
        )

    if lead.get("qualification_readiness_status"):
        st.write(
            f"**Qualification Readiness:** "
            f"{lead['qualification_readiness_status']} "
            f"({lead['qualification_readiness_score']:.0f}/100)"
        )

    if lead.get("sales_motion"):
        st.write(
            f"**Upstream Sales Motion:** "
            f"{lead['sales_motion']}"
        )

    if lead.get("buyer_access_status"):
        st.write(
            f"**Buyer Access:** "
            f"{lead['buyer_access_status']}"
        )


# ---------------------------------------------------------------------
# OUTREACH STRATEGY
# ---------------------------------------------------------------------

with profile_col_3:

    st.markdown(
        "#### 📨 Outreach Strategy"
    )

    st.write(
        f"**Mode:** "
        f"{strategy['mode']}"
    )

    st.write(
        f"**Priority:** "
        f"{strategy['priority']}"
    )

    st.write(
        f"**Intensity:** "
        f"{strategy['intensity']}"
    )

    st.write(
        f"**Language:** "
        f"{strategy['language']}"
    )

    st.write(
        f"**Primary Channel:** "
        f"{strategy['primary_channel']}"
    )

    st.write(
        "**Cadence:** "
        + " → ".join(
            f"Day +{day}"
            for day
            in strategy[
                "cadence_days"
            ]
        )
    )

    if lead.get("territory_profile_id"):
        st.write(
            f"**Field Motion:** "
            f"{strategy.get('field_motion', '')}"
        )

        if strategy.get("territory_language_note"):
            st.caption(strategy["territory_language_note"])


# ---------------------------------------------------------------------
# UPSTREAM QUALIFICATION INTELLIGENCE
# ---------------------------------------------------------------------

if (
    lead.get("sales_motion")
    or lead.get("qualification_readiness_status")
    or lead.get("commercial_hypothesis")
):
    st.divider()
    st.subheader("🔎 Upstream Qualification Intelligence")
    st.caption(
        "Evidence and open questions carried forward from IDENTIFY. "
        "These are internal execution inputs, not prospect-facing claims."
    )

    uq1, uq2, uq3 = st.columns(3)
    with uq1:
        st.metric(
            "Qualification Readiness",
            (
                f"{lead['qualification_readiness_score']:.0f}/100"
                if lead.get("qualification_readiness_score")
                else "N/A"
            ),
        )
    with uq2:
        render_status_card(
            "Sales Motion",
            lead.get("sales_motion"),
            "Internal execution stage carried forward from IDENTIFY.",
        )
    with uq3:
        render_status_card(
            "Buyer Access",
            lead.get("buyer_access_status"),
            "Observed public access path; authority may still require validation.",
        )

    intel_left, intel_right = st.columns(2)

    with intel_left:
        if lead.get("commercial_hypothesis"):
            render_card(
                "Commercial Hypothesis",
                lead["commercial_hypothesis"],
                "🧩",
            )

        if lead.get("commercial_angle"):
            render_card(
                "Evidence-Based Commercial Angle",
                lead["commercial_angle"],
                "🧭",
            )

        if lead.get("next_best_action"):
            render_card(
                "Next Best Action",
                lead["next_best_action"],
                "🎯",
            )

    with intel_right:
        if lead.get("sales_evidence_gaps"):
            render_list_card(
                "Evidence Gaps To Validate",
                lead["sales_evidence_gaps"],
                "🔍",
            )

        if lead.get("qualification_questions"):
            render_list_card(
                "Qualification Questions",
                lead["qualification_questions"],
                "❓",
            )

        if lead.get("commercial_risk_flags"):
            render_list_card(
                "Validation Flags",
                lead["commercial_risk_flags"],
                "⚠️",
            )

    if lead.get("sales_intelligence_basis"):
        st.caption(lead["sales_intelligence_basis"])


# ---------------------------------------------------------------------
# ADAPTIVE CADENCE
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "🗓️ Adaptive Cadence"
)


st.caption(
    "Timing changes according to commercial priority, "
    "engagement signal and proposal context."
)


touch_columns = st.columns(
    4
)


for (
    column,
    touch_number,
    touch,
) in zip(

    touch_columns,

    range(
        1,
        5,
    ),

    strategy[
        "touches"
    ],
):

    with column:

        with st.container(
            border=True
        ):

            st.markdown(
                f"**Touch {touch_number}**"
            )

            st.markdown(
                f"### Day +"
                f"{touch['offset_days']}"
            )

            st.write(
                touch[
                    "name"
                ]
            )

            st.caption(
                f"{touch_channel(strategy['primary_channel'], touch_number)}"
                f" · "
                f"{touch['goal']}"
            )


# ---------------------------------------------------------------------
# COMMERCIAL DECISION SUPPORT
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "🧠 Commercial Decision Support"
)


decision_1, decision_2 = st.columns(
    2
)


with decision_1:

    render_card(

        "Recommended Action",

        (
            lead.get(
                "recommended_action"
            )
            or (
                "Execute the adaptive outreach cadence "
                "and validate the next commercial step."
            )
        ),

        "🎯",
    )


    render_card(

        "Commercial Objective",

        strategy[
            "commercial_objective"
        ],

        "🚀",
    )

    if lead.get("outreach_angle"):
        render_card(
            "Upstream Outreach Angle",
            lead["outreach_angle"],
            "🧭",
        )

    if lead.get("contact_outreach_angle"):
        render_card(
            "Contact-Specific Angle",
            lead["contact_outreach_angle"],
            "👤",
        )


    render_card(

        "Suggested Stakeholder Function",

        stakeholder_function(
            lead[
                "industry"
            ]
        ),

        "👤",
    )


with decision_2:

    render_card(

        "Score Rationale",

        (
            lead.get(
                "score_rationale"
            )
            or (
                "No upstream scoring rationale was supplied. "
                "The account is being managed using available outreach signals."
            )
        ),

        "🔎",
    )


    render_card(

        "Decision Risk",

        decision_risk(
            lead,
            strategy[
                "priority"
            ],
        ),

        "⚠️",
    )


    render_card(

        "Communication Profile",

        (
            f"Language: "
            f"{strategy['language']}\n"

            f"Channel: "
            f"{strategy['primary_channel']}\n"

            f"Tone: "
            f"{strategy['tone']}"
        ),

        "🌍",
    )


# ---------------------------------------------------------------------
# ADAPTIVE SEQUENCE GENERATOR
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "✍️ Adaptive Outreach Sequence"
)


if ai_enabled:

    st.caption(
        "AI-assisted copy generation is enabled. "
        "The deterministic engine remains the source of truth "
        "for priority, cadence and channel logic."
    )

else:

    st.caption(
        "No AI API key is configured. "
        "The deterministic local fallback will generate the sequence."
    )


sequence_state_key = (
    "generated_outreach_sequence"
)


company_state_key = (
    "generated_outreach_company"
)


sequence_status_key = (
    "generated_outreach_status"
)


if st.button(
    "Generate Adaptive Outreach Sequence",
    type="primary",
    use_container_width=True,
):

    try:

        with st.spinner(
            "Generating outreach sequence..."
        ):

            if ai_enabled:

                sequence = generate_sequence(
                    lead,
                    profile,
                )

            else:

                sequence = generate_local_sequence(
                    lead,
                    profile,
                    strategy,
                )

        if (
            not isinstance(sequence, dict)
            or not sequence
        ):

            raise ValueError(
                "The generator returned an empty sequence."
            )

        required_sequence_keys = {
            "day_1",
            "day_3",
            "day_7",
            "day_14",
        }

        missing_sequence_keys = (
            required_sequence_keys
            - set(sequence.keys())
        )

        if missing_sequence_keys:

            raise ValueError(
                "The generated sequence is missing: "
                + ", ".join(
                    sorted(missing_sequence_keys)
                )
            )

        st.session_state[
            sequence_state_key
        ] = sequence

        st.session_state[
            company_state_key
        ] = lead[
            "company"
        ]

        st.session_state[
            sequence_status_key
        ] = (
            f"Sequence generated successfully for {lead['company']}. "
            "The four outreach touches are shown directly below."
        )

    except Exception as exc:

        st.session_state.pop(
            sequence_state_key,
            None,
        )

        st.session_state.pop(
            company_state_key,
            None,
        )

        st.session_state[
            sequence_status_key
        ] = (
            "ERROR: "
            + str(exc)
        )


sequence_status = st.session_state.get(
    sequence_status_key,
    "",
)


if sequence_status:

    if sequence_status.startswith(
        "ERROR:"
    ):

        st.error(
            sequence_status
        )

    else:

        st.success(
            sequence_status
        )
        st.caption(
            "Prospect-facing copy is generated from observed evidence and open "
            "qualification questions. Internal scores and readiness labels are not exposed."
        )


# ---------------------------------------------------------------------
# SHOW GENERATED SEQUENCE
# ---------------------------------------------------------------------

if (

    st.session_state.get(
        sequence_state_key
    )

    and

    st.session_state.get(
        company_state_key
    )
    == lead[
        "company"
    ]

):

    sequence = st.session_state[
        sequence_state_key
    ]


    tab_labels = [

        data.get(
            "timing",
            f"Touch {index}",
        )

        for index, data
        in enumerate(
            sequence.values(),
            start=1,
        )
    ]


    tabs = st.tabs(
        tab_labels
    )


    for tab, data in zip(

        tabs,

        sequence.values(),
    ):

        with tab:

            st.markdown(
                f"### "
                f"{data.get('label', 'Outreach Touch')}"
            )


            meta_1, meta_2 = st.columns(
                2
            )


            with meta_1:

                render_card(
                    "Timing",
                    data.get(
                        "timing",
                        "",
                    ),
                    "🗓️",
                )


            with meta_2:

                render_card(
                    "Channel",
                    data.get(
                        "channel",
                        "",
                    ),
                    "📡",
                )


            if data.get(
                "subject"
            ):

                render_card(
                    "Subject",
                    data[
                        "subject"
                    ],
                    "✉️",
                )


            render_card(

                "Message",

                data.get(
                    "message",
                    "",
                ),

                "💬",
            )


    output_text = sequence_to_text(
        lead[
            "company"
        ],
        sequence,
    )


    sequence_rows = pd.DataFrame(
        [
            {
                "timing": data.get("timing", ""),
                "label": data.get("label", ""),
                "channel": data.get("channel", ""),
                "subject": data.get("subject", ""),
                "message": data.get("message", ""),
            }
            for data in sequence.values()
        ]
    )

    download_text_col, download_csv_col = st.columns(2)

    with download_text_col:
        st.download_button(
            "⬇ Download Sequence — TXT",
            output_text,
            file_name=(
                f"{safe_filename(lead['company'])}"
                "_adaptive_outreach_sequence.txt"
            ),
            mime="text/plain",
            use_container_width=True,
        )

    with download_csv_col:
        st.download_button(
            "⬇ Download Sequence — CSV",
            sequence_rows.to_csv(index=False).encode("utf-8"),
            file_name=(
                f"{safe_filename(lead['company'])}"
                "_adaptive_outreach_sequence.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )


# ---------------------------------------------------------------------
# BUSINESS DEVELOPMENT EXECUTION
# ---------------------------------------------------------------------

st.divider()
st.subheader("📈 Business Development Execution Log")
st.caption(
    "Continue the commercial process after outreach: record responses, meetings, "
    "qualification evidence, objections and the next action without losing the mandate context."
)

execution_key = f"bd_execution::{safe_filename(lead['company'])}"

with st.form(f"bd_execution_form::{safe_filename(lead['company'])}"):
    exec_1, exec_2 = st.columns(2)

    with exec_1:
        opportunity_stage = st.selectbox(
            "Opportunity stage",
            OPPORTUNITY_STAGES,
            index=0,
        )
        response_status = st.selectbox(
            "Response status",
            RESPONSE_STATUSES,
            index=0,
        )
        meeting_outcome = st.text_area(
            "Meeting / conversation outcome",
            height=80,
            placeholder="What was learned? What changed after the conversation?",
        )
        commercial_interest = st.text_area(
            "Commercial interest / use case",
            height=80,
            placeholder="Observed interest only; do not infer demand that was not expressed.",
        )
        products_discussed = st.text_input(
            "Products / solutions discussed",
        )
        budget_status = st.text_input(
            "Budget / investment status",
            placeholder="Unknown / exploratory / budgeted / to validate",
        )
        timeline = st.text_input(
            "Commercial timeline",
            placeholder="e.g. Q1 2027 / 3–6 months / no timing yet",
        )

    with exec_2:
        decision_process = st.text_area(
            "Decision process / stakeholders",
            height=80,
        )
        technical_questions = st.text_area(
            "Technical / feasibility questions",
            height=80,
        )
        objections = st.text_area(
            "Objections / blockers",
            height=80,
        )
        documents_requested = st.text_area(
            "Documents / information requested",
            height=80,
        )
        next_action = st.text_input(
            "Next commercial action",
            placeholder="Send technical sheet, schedule demo, qualify distributor...",
        )
        next_action_date = st.date_input(
            "Next action date",
            value=None,
        )
        execution_notes = st.text_area(
            "Execution notes",
            height=80,
        )

    save_execution = st.form_submit_button(
        "Save Execution Update",
        type="primary",
        use_container_width=True,
    )

if save_execution:
    execution_update = build_execution_update(
        lead,
        opportunity_stage=opportunity_stage,
        response_status=response_status,
        meeting_outcome=meeting_outcome,
        commercial_interest=commercial_interest,
        products_discussed=products_discussed,
        decision_process=decision_process,
        budget_status=budget_status,
        timeline=timeline,
        technical_questions=technical_questions,
        objections=objections,
        documents_requested=documents_requested,
        next_action=next_action,
        next_action_date=str(next_action_date or ""),
        execution_notes=execution_notes,
    )
    st.session_state[execution_key] = execution_update

execution_update = st.session_state.get(execution_key)

if execution_update:
    execution_df = pd.DataFrame([execution_update])
    e1, e2, e3 = st.columns(3)
    e1.metric("Stage", execution_update.get("opportunity_stage", ""))
    e2.metric("Response", execution_update.get("response_status", ""))
    e3.metric(
        "Next Action",
        execution_update.get("next_action", "") or "To define",
    )

    st.download_button(
        "⬇ Download BD Execution Update",
        execution_df.to_csv(index=False).encode("utf-8"),
        file_name=(
            f"{safe_filename(lead['company'])}"
            "_bd_execution_update.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# COMMERCIAL DEAL SHEET
# ---------------------------------------------------------------------

st.divider()
st.subheader("💼 Commercial Deal Sheet")
st.caption(
    "Structure an active opportunity without turning commercial assumptions into facts. "
    "Use only terms that were discussed, quoted or otherwise verified."
)

deal_key = f"commercial_deal::{safe_filename(lead['company'])}"

with st.form(f"commercial_deal_form::{safe_filename(lead['company'])}"):
    deal_1, deal_2 = st.columns(2)

    with deal_1:
        deal_stage = st.selectbox(
            "Deal stage",
            DEAL_STAGES,
            index=0,
        )
        deal_product = st.text_input(
            "Product / solution",
            value=optional(lead.get("mandate_product"), ""),
        )
        product_specification = st.text_area(
            "Product / technical scope",
            height=80,
        )
        deal_quantity = st.text_input(
            "Quantity / scope",
        )
        value_col, currency_col = st.columns([2, 1])
        with value_col:
            deal_indicative_value = st.number_input(
                "Indicative commercial value",
                min_value=0.0,
                value=0.0,
                step=1000.0,
            )
        with currency_col:
            deal_currency = st.selectbox(
                "Currency",
                ["EUR", "USD", "BRL", "GBP", "Other"],
            )
        quotation_status = st.text_input(
            "Quotation / proposal status",
            placeholder="Not issued / requested / submitted / under review",
        )
        incoterm = st.text_input(
            "Incoterm",
            placeholder="e.g. EXW / FCA / FOB / CIF — if discussed",
        )
        payment_terms = st.text_input(
            "Payment terms",
        )
        moq = st.text_input(
            "MOQ / minimum order",
        )

    with deal_2:
        delivery_terms = st.text_area(
            "Delivery / lead-time terms",
            height=70,
        )
        warranty_terms = st.text_area(
            "Warranty terms",
            height=70,
        )
        after_sales_model = st.text_area(
            "After-sales / technical support model",
            height=70,
        )
        exclusivity_terms = st.text_input(
            "Exclusivity terms",
        )
        territory_terms = st.text_input(
            "Territory terms",
        )
        commission_terms = st.text_input(
            "Commission / success-fee terms",
        )
        technical_validation = st.text_area(
            "Technical validation status",
            height=70,
        )
        regulatory_validation = st.text_area(
            "Regulatory / customs validation status",
            height=70,
        )

    documents_exchanged = st.text_area(
        "Documents exchanged",
        placeholder="Technical sheet, quotation, NDA, drawings, certificates...",
        height=70,
    )
    decision_makers = st.text_area(
        "Decision makers / stakeholders",
        height=70,
    )
    commercial_risks = st.text_area(
        "Commercial risks / open issues",
        height=70,
    )
    next_step_col, next_date_col = st.columns([2, 1])
    with next_step_col:
        deal_next_step = st.text_input(
            "Deal next step",
        )
    with next_date_col:
        deal_next_step_date = st.date_input(
            "Deal next-step date",
            value=None,
        )
    deal_notes = st.text_area(
        "Deal notes",
        height=80,
    )

    save_deal = st.form_submit_button(
        "Save Commercial Deal Sheet",
        type="primary",
        use_container_width=True,
    )

if save_deal:
    commercial_deal = build_commercial_deal_sheet(
        lead,
        deal_stage=deal_stage,
        product=deal_product,
        product_specification=product_specification,
        quantity=deal_quantity,
        indicative_value=deal_indicative_value,
        currency=deal_currency,
        quotation_status=quotation_status,
        incoterm=incoterm,
        payment_terms=payment_terms,
        moq=moq,
        delivery_terms=delivery_terms,
        warranty_terms=warranty_terms,
        after_sales_model=after_sales_model,
        exclusivity_terms=exclusivity_terms,
        territory_terms=territory_terms,
        commission_terms=commission_terms,
        technical_validation=technical_validation,
        regulatory_validation=regulatory_validation,
        documents_exchanged=documents_exchanged,
        decision_makers=decision_makers,
        commercial_risks=commercial_risks,
        next_step=deal_next_step,
        next_step_date=str(deal_next_step_date or ""),
        deal_notes=deal_notes,
    )
    st.session_state[deal_key] = commercial_deal

commercial_deal = st.session_state.get(deal_key)

if commercial_deal:
    deal_df = pd.DataFrame([commercial_deal])
    d1, d2, d3 = st.columns(3)
    d1.metric("Deal Stage", commercial_deal.get("deal_stage", ""))
    deal_value = float(commercial_deal.get("deal_indicative_value", 0) or 0)
    deal_currency_display = commercial_deal.get("deal_currency", "")
    d2.metric(
        "Indicative Value",
        (
            f"{deal_currency_display} {deal_value:,.0f}"
            if deal_value > 0
            else "To qualify"
        ),
    )
    d3.metric(
        "Deal Next Step",
        commercial_deal.get("deal_next_step", "") or "To define",
    )

    st.download_button(
        "⬇ Download Commercial Deal Sheet",
        deal_df.to_csv(index=False).encode("utf-8"),
        file_name=(
            f"{safe_filename(lead['company'])}"
            "_commercial_deal_sheet.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# COMMERCIAL MANDATE REPORTING
# ---------------------------------------------------------------------

st.divider()
st.subheader("📊 Commercial Mandate Reporting")
st.caption(
    "Operational reporting from the pipeline and the execution / deal records entered "
    "in this session. Counts reflect recorded activity only."
)

execution_updates = [
    value
    for key, value in st.session_state.items()
    if str(key).startswith("bd_execution::")
    and isinstance(value, dict)
]

deal_sheets = [
    value
    for key, value in st.session_state.items()
    if str(key).startswith("commercial_deal::")
    and isinstance(value, dict)
]

mandate_report = build_mandate_report(
    df,
    execution_updates=execution_updates,
    deal_sheets=deal_sheets,
)

if mandate_report.get("mandate_summary"):
    st.markdown(
        "**Mandate:** " + mandate_report["mandate_summary"]
    )

mr1, mr2, mr3, mr4 = st.columns(4)
mr1.metric(
    "Counterparties",
    mandate_report["total_counterparties"],
)
mr2.metric(
    "Qualified",
    mandate_report["qualified_counterparties"],
)
mr3.metric(
    "Responses",
    mandate_report["responses"],
)
mr4.metric(
    "Active Opportunities",
    mandate_report["active_opportunities"],
)

mr5, mr6, mr7, mr8 = st.columns(4)
mr5.metric("Contacted", mandate_report["contacted"])
mr6.metric("Meetings", mandate_report["meetings"])
mr7.metric("Quotations", mandate_report["quotations"])
mr8.metric("Won", mandate_report["won"])

pipeline_values = mandate_report.get(
    "pipeline_value_by_currency",
    {},
)
if pipeline_values:
    st.markdown("**Indicative opportunity value entered**")
    st.write(
        " · ".join(
            f"{currency} {value:,.0f}"
            for currency, value in pipeline_values.items()
        )
    )

pending_actions = mandate_report.get("pending_actions", [])
if pending_actions:
    st.markdown("**Next-action queue**")
    st.dataframe(
        pd.DataFrame(pending_actions),
        hide_index=True,
        use_container_width=True,
    )

report_markdown = report_to_markdown(mandate_report)
report_col, execution_col, deals_col = st.columns(3)

with report_col:
    st.download_button(
        "⬇ Mandate Report — Markdown",
        report_markdown,
        file_name="commercial_mandate_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

with execution_col:
    if execution_updates:
        st.download_button(
            "⬇ Execution Log — CSV",
            pd.DataFrame(execution_updates)
            .to_csv(index=False)
            .encode("utf-8"),
            file_name="bd_execution_log.csv",
            mime="text/csv",
            use_container_width=True,
        )

with deals_col:
    if deal_sheets:
        st.download_button(
            "⬇ Deal Pipeline — CSV",
            pd.DataFrame(deal_sheets)
            .to_csv(index=False)
            .encode("utf-8"),
            file_name="commercial_deal_pipeline.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.caption(
    "Reporting metrics are workflow indicators from recorded activity. "
    "They are not market-size, demand or conversion-rate claims."
)


# ---------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------

st.divider()


st.caption(
    "Ambrosin BD workflow: COMMERCIAL MANDATE → IDENTIFY → PRIORITIZE / PARTNER "
    "→ ENGAGE → QUALIFIED DIALOGUE → OPPORTUNITY → NEXT ACTION"
)
