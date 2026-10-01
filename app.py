import html
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from field_planner import build_field_day_plan
from outreach_generator import (
    COUNTRY_PROFILE,
    DEFAULT_PROFILE,
    build_outreach_strategy,
    generate_local_sequence,
    generate_sequence,
    normalize_lead,
)


st.set_page_config(
    page_title="Adaptive Outreach Intelligence",
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
    "📨 Adaptive Outreach Intelligence Platform"
)

st.caption(
    "Turn pipeline context into prioritized, multilingual and adaptive "
    "commercial outreach for Business Development, GTM and Partnerships."
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
        "Standard outreach CSVs and exports from the "
        "Lead Qualification & Revenue Prioritization Platform are supported."
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
# EXECUTIVE OUTREACH DASHBOARD
# ---------------------------------------------------------------------

st.divider()


st.subheader(
    "👔 Executive Outreach Dashboard"
)


st.caption(
    "Prioritize commercial attention using qualification context, "
    "engagement signals, proposal timing and adaptive outreach strategy."
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
    "🧩 Account & Outreach Intelligence Workspace"
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
# FOOTER
# ---------------------------------------------------------------------

st.divider()


st.caption(
    "Commercial Intelligence workflow: "
    "IDENTIFY → PRIORITIZE → ENGAGE → LEARN → ADVANCE"
)
