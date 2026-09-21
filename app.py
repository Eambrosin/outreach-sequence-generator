import html
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from outreach_generator import (
    COUNTRY_PROFILE,
    DEFAULT_PROFILE,
    build_outreach_strategy,
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
score_rationale""",
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
    "🧩 Outreach Intelligence Workspace"
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
    "✍️ Adaptive Sequence Generator"
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


if st.button(
    "Generate Adaptive Outreach Sequence",
    type="primary",
):

    with st.spinner(
        "Generating outreach sequence..."
    ):

        sequence = generate_sequence(
            lead,
            profile,
        )


    st.session_state[
        sequence_state_key
    ] = sequence


    st.session_state[
        company_state_key
    ] = lead[
        "company"
    ]


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


    st.download_button(

        "⬇ Download Outreach Sequence",

        output_text,

        file_name=(
            f"{safe_filename(lead['company'])}"
            "_adaptive_outreach_sequence.txt"
        ),

        mime=(
            "text/plain"
        ),
    )


# ---------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------

st.divider()


st.caption(
    "Commercial Intelligence workflow: "
    "Qualify → Prioritize → Engage → Learn → Advance"
)
