import os
import re
import pandas as pd
import streamlit as st

from outreach_generator import COUNTRY_PROFILE, DEFAULT_PROFILE


st.set_page_config(
    page_title="AI Outreach Sequence Generator",
    page_icon="📨",
    layout="wide",
)


def format_money(value):
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return str(value)


def get_profile(country):
    return COUNTRY_PROFILE.get(country, DEFAULT_PROFILE)


def safe_filename(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def local_sequence(lead, profile):
    company = lead["company"]
    contact = lead["contact_name"]
    country = lead["country"]
    industry = lead["industry"]
    deal_type = lead["deal_type"]
    deal_value = format_money(lead["deal_value_usd"])
    sender = lead["your_name"]

    return {
        "Day 1 — Soft Check-in": {
            "channel": profile["channel"],
            "subject": f"Following up on {deal_type}",
            "message": f"""Hi {contact},

I wanted to follow up on the {deal_type} we shared with {company}.

Given your work in {industry} and the opportunity size of {deal_value}, I thought it would be useful to check whether you had a chance to review it.

Happy to clarify any point or adjust the next step if helpful.

Best,
{sender}""",
        },
        "Day 3 — Value Add": {
            "channel": profile["channel"],
            "subject": f"Potential value for {company}",
            "message": f"""Hi {contact},

One reason I thought this could be relevant for {company} is the potential to support growth, commercial efficiency or partnership development in {country}.

For companies in {industry}, timing and prioritization often make a big difference when evaluating opportunities like this.

Would it be useful if I shared a short summary of the main business case?

Best,
{sender}""",
        },
        "Day 7 — Re-engagement": {
            "channel": profile["channel"],
            "subject": f"Quick question on next steps",
            "message": f"""Hi {contact},

Quick question: is the {deal_type} still something relevant for your team to evaluate?

If yes, I would be happy to align on the most useful next step.

If priorities have changed, no problem at all.

Best,
{sender}""",
        },
        "Day 14 — Final Touch": {
            "channel": profile["channel"],
            "subject": f"Closing the loop",
            "message": f"""Hi {contact},

I wanted to close the loop on the proposal shared with {company}.

If this is not a current priority, I completely understand. If timing becomes more relevant later, I would be glad to reconnect.

Thanks again for your time.

Best,
{sender}""",
        },
    }


def render_card(title, content, icon="📌"):
    st.markdown(f"### {icon} {title}")
    st.markdown(
        f"""
<div style="
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 18px;
    background-color: #ffffff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    white-space: pre-wrap;
    line-height: 1.6;
">{str(content).strip()}</div>
        """,
        unsafe_allow_html=True,
    )


def sequence_to_text(company, sequence):
    lines = [f"Outreach Sequence — {company}", ""]
    for step, data in sequence.items():
        lines.append(step)
        lines.append(f"Channel: {data['channel']}")
        if data.get("subject"):
            lines.append(f"Subject: {data['subject']}")
        lines.append("")
        lines.append(data["message"])
        lines.append("")
        lines.append("-" * 60)
        lines.append("")
    return "\n".join(lines)


st.title("📨 AI Outreach Sequence Generator")
st.caption("Generate multilingual, market-aware follow-up sequences for Business Development, Sales and Partnerships teams.")

uploaded = st.file_uploader("Upload Pipeline CSV", type=["csv"])

if uploaded is not None:
    df = pd.read_csv(uploaded)
else:
    df = pd.read_csv("data/pipeline.csv")

required_columns = [
    "contact_name",
    "company",
    "country",
    "industry",
    "deal_type",
    "deal_value_usd",
    "proposal_sent_days_ago",
    "your_name",
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("Missing columns in CSV: " + ", ".join(missing_columns))
    st.stop()

st.subheader("📊 Executive Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accounts", len(df))
col2.metric("Pipeline Value", f"${df['deal_value_usd'].sum():,.0f}")
col3.metric("Countries", df["country"].nunique())
col4.metric("Deal Types", df["deal_type"].nunique())

st.divider()
st.subheader("👔 Executive Outreach Dashboard")
st.caption("Executive view of follow-up urgency, revenue exposure and channel strategy.")

df_dashboard = df.copy()

df_dashboard["follow_up_priority_score"] = (
    df_dashboard["deal_value_usd"].rank(pct=True) * 50
    + df_dashboard["proposal_sent_days_ago"].rank(pct=True) * 50
).round(1)

df_dashboard["priority_level"] = df_dashboard["follow_up_priority_score"].apply(
    lambda score: "High" if score >= 75 else "Medium" if score >= 50 else "Low"
)

df_dashboard["recommended_channel"] = df_dashboard["country"].apply(
    lambda country: get_profile(country)["channel"]
)

df_dashboard["revenue_at_risk"] = df_dashboard.apply(
    lambda row: row["deal_value_usd"] if row["proposal_sent_days_ago"] >= 7 else 0,
    axis=1
)

high_priority_accounts = len(df_dashboard[df_dashboard["priority_level"] == "High"])
revenue_at_risk = df_dashboard["revenue_at_risk"].sum()
avg_days_waiting = round(df_dashboard["proposal_sent_days_ago"].mean(), 1)
top_priority = df_dashboard.sort_values("follow_up_priority_score", ascending=False).iloc[0]

exec_col_1, exec_col_2, exec_col_3, exec_col_4 = st.columns(4)

exec_col_1.metric("High Priority Accounts", high_priority_accounts)
exec_col_2.metric("Revenue At Risk", f"${revenue_at_risk:,.0f}")
exec_col_3.metric("Avg. Days Waiting", avg_days_waiting)
exec_col_4.metric("Top Follow-up Priority", top_priority["company"])

st.markdown("#### 📈 Follow-up Priority Ranking")

priority_table = df_dashboard.sort_values(
    "follow_up_priority_score",
    ascending=False
)[
    [
        "company",
        "country",
        "industry",
        "deal_type",
        "deal_value_usd",
        "proposal_sent_days_ago",
        "recommended_channel",
        "follow_up_priority_score",
        "priority_level",
    ]
]

st.dataframe(priority_table, width="stretch")

priority_csv = priority_table.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Follow-up Priority CSV",
    priority_csv,
    "follow_up_priority_ranking.csv",
    "text/csv",
)

st.markdown("#### 📨 Recommended Channel Mix")

channel_mix = (
    df_dashboard["recommended_channel"]
    .value_counts()
    .reset_index()
)
channel_mix.columns = ["channel", "accounts"]
st.dataframe(channel_mix, width="stretch")

st.markdown("#### Executive Interpretation")

st.write(
    f"Initial follow-up focus should be on **{top_priority['company']}**, which has the highest combination "
    f"of deal value and time since proposal was sent."
)

if revenue_at_risk > 0:
    st.write(
        f"There is currently **${revenue_at_risk:,.0f}** in revenue at risk from opportunities waiting "
        f"7 or more days after proposal."
    )
else:
    st.write("No major revenue-at-risk exposure detected based on the current follow-up timing.")

st.divider()


st.subheader("🎯 Pipeline Overview")
st.dataframe(df, width="stretch")

st.divider()

st.subheader("🧩 Outreach Workspace")

selected_company = st.selectbox("Select an account", df["company"].tolist())
selected_row = df[df["company"] == selected_company].iloc[0]
lead = selected_row.to_dict()
profile = get_profile(lead["country"])

profile_col_1, profile_col_2, profile_col_3 = st.columns(3)

with profile_col_1:
    st.markdown("#### 🏢 Account Profile")
    st.write(f"**Company:** {lead['company']}")
    st.write(f"**Contact:** {lead['contact_name']}")
    st.write(f"**Country:** {lead['country']}")
    st.write(f"**Industry:** {lead['industry']}")

with profile_col_2:
    st.markdown("#### 💰 Deal Context")
    st.write(f"**Deal Type:** {lead['deal_type']}")
    st.write(f"**Deal Value:** {format_money(lead['deal_value_usd'])}")
    st.write(f"**Proposal Sent:** {lead['proposal_sent_days_ago']} days ago")
    st.write(f"**Sender:** {lead['your_name']}")

with profile_col_3:
    st.markdown("#### 🌍 Communication Strategy")
    st.write(f"**Language:** {profile['language']}")
    st.write(f"**Recommended Channel:** {profile['channel']}")
    st.write(f"**Tone:** {profile['tone']}")

st.divider()
st.subheader("🧠 Business Development Intelligence Layer")
st.caption("Commercial interpretation of the selected account before generating the sequence.")

bd_col_1, bd_col_2, bd_col_3 = st.columns(3)

with bd_col_1:
    st.markdown("#### �� Recommended Motion")
    if lead["proposal_sent_days_ago"] >= 7:
        st.warning("Urgent follow-up. Proposal has been waiting for 7+ days.")
    elif lead["proposal_sent_days_ago"] >= 3:
        st.info("Active follow-up. Add value and create momentum.")
    else:
        st.success("Soft check-in. Keep the tone light and relationship-oriented.")

with bd_col_2:
    st.markdown("#### 🤝 Partnership Potential")
    if lead["deal_value_usd"] >= df["deal_value_usd"].quantile(0.75):
        st.write("High partnership potential due to strong deal value and strategic account relevance.")
    else:
        st.write("Moderate partnership potential. Continue qualification before escalating.")

with bd_col_3:
    st.markdown("#### ⚠️ Decision Risk")
    if lead["proposal_sent_days_ago"] >= 10:
        st.write("High risk. The opportunity may be losing momentum.")
    elif lead["proposal_sent_days_ago"] >= 5:
        st.write("Medium risk. A clear next step should be proposed.")
    else:
        st.write("Low risk. The proposal is still recent.")

st.markdown("#### Suggested Stakeholder Angle")

if lead["industry"] in ["Agribusiness", "Logistics & Trade"]:
    st.write("Focus on commercial, procurement or international trade stakeholders.")
elif lead["industry"] in ["Fintech", "Renewable Energy"]:
    st.write("Focus on strategy, partnerships, innovation or growth stakeholders.")
elif lead["industry"] == "Real Estate":
    st.write("Focus on investment, partnerships or business development stakeholders.")
else:
    st.write("Focus on the stakeholder responsible for growth, partnerships or commercial execution.")

st.divider()
st.subheader("🤖 AI Outreach Intelligence")
st.caption("Strategic account interpretation for Business Development, Partnerships and GTM follow-up.")

def urgency_level(days):
    if days >= 10:
        return "High"
    if days >= 5:
        return "Medium"
    return "Low"


def revenue_tier(value):
    if value >= df["deal_value_usd"].quantile(0.75):
        return "High"
    if value >= df["deal_value_usd"].quantile(0.40):
        return "Medium"
    return "Low"


def commercial_opportunity(lead):
    return (
        f"{lead['company']} represents a {revenue_tier(lead['deal_value_usd']).lower()}-value opportunity "
        f"in {lead['industry']} with a proposal already sent {lead['proposal_sent_days_ago']} days ago. "
        f"The key commercial objective is to re-engage the account, validate decision timing and move the opportunity "
        f"toward a clear next step."
    )


def expansion_hypothesis(lead):
    if lead["country"] in ["Colombia", "Mexico", "Brazil", "Argentina"]:
        return (
            f"{lead['company']} may be relevant for LATAM expansion discussions, especially around distribution, "
            f"commercial partnerships, regional growth and market access."
        )
    if lead["country"] in ["UAE", "Saudi Arabia", "Qatar", "Kuwait", "Oman", "Bahrain"]:
        return (
            f"{lead['company']} may be relevant for MENA expansion, where trust, long-term relationship building "
            f"and partnership credibility are key to advancing commercial conversations."
        )
    return (
        f"{lead['company']} may be relevant for market expansion or partnership development depending on current "
        f"growth priorities and stakeholder alignment."
    )


def partnership_hypothesis(lead):
    if lead["industry"] in ["Logistics & Trade", "Agribusiness"]:
        return "Potential partnership angle: distribution channels, trade facilitation, supply partnerships or cross-border commercial execution."
    if lead["industry"] == "Fintech":
        return "Potential partnership angle: market access, financial infrastructure, embedded services or strategic commercial alliances."
    if lead["industry"] == "Renewable Energy":
        return "Potential partnership angle: project development, equipment supply, regional deployment or strategic energy partnerships."
    if lead["industry"] == "Real Estate":
        return "Potential partnership angle: investment access, asset partnerships, co-development or commercial introductions."
    return "Potential partnership angle: growth collaboration, market access or strategic commercial alignment."


def recommended_outreach_strategy(lead, profile):
    days = lead["proposal_sent_days_ago"]

    if days >= 10:
        return (
            f"Use a concise final-touch follow-up through {profile['channel']}. Acknowledge that timing may have changed, "
            f"leave the door open and ask whether the proposal should be adjusted or revisited later."
        )
    if days >= 5:
        return (
            f"Use a value-add follow-up through {profile['channel']}. Reconnect the proposal to business outcomes, "
            f"ask one easy question and propose a clear next step."
        )
    return (
        f"Use a soft check-in through {profile['channel']}. Confirm receipt, keep the tone light and invite questions "
        f"without creating pressure."
    )


def suggested_stakeholder(lead):
    if lead["industry"] in ["Agribusiness", "Logistics & Trade"]:
        return "Commercial Director, Procurement Lead, International Trade Manager or Business Development Lead."
    if lead["industry"] in ["Fintech", "Renewable Energy"]:
        return "Head of Partnerships, Strategy Lead, Growth Lead or Business Development Director."
    if lead["industry"] == "Real Estate":
        return "Investment Director, Partnerships Lead, Asset Manager or Business Development Manager."
    return "Business Development, Partnerships, Strategy or Commercial leadership."


def risk_assessment(lead):
    days = lead["proposal_sent_days_ago"]
    value = lead["deal_value_usd"]

    if days >= 10 and value >= df["deal_value_usd"].quantile(0.75):
        return "High risk: high-value opportunity with extended silence after proposal. Requires immediate executive-level follow-up."
    if days >= 7:
        return "Medium-high risk: proposal has been waiting for a week or more. Momentum may be declining."
    if days >= 3:
        return "Medium risk: appropriate moment to add value and re-engage before the opportunity slows down."
    return "Low risk: proposal is recent. Keep follow-up consultative and relationship-oriented."


ai_sections = {
    "Account Summary": (
        f"{lead['company']} is a {lead['country']}-based account in {lead['industry']} with a "
        f"{format_money(lead['deal_value_usd'])} {lead['deal_type']} opportunity. The proposal was sent "
        f"{lead['proposal_sent_days_ago']} days ago."
    ),
    "Why This Account Matters": (
        f"This account matters because it combines commercial value, international market context and an active proposal stage. "
        f"It should be managed as a structured follow-up opportunity rather than a generic outbound lead."
    ),
    "Commercial Opportunity": commercial_opportunity(lead),
    "Expansion Hypothesis": expansion_hypothesis(lead),
    "Partnership Hypothesis": partnership_hypothesis(lead),
    "Recommended Outreach Strategy": recommended_outreach_strategy(lead, profile),
    "Suggested Stakeholder": suggested_stakeholder(lead),
    "Risk Assessment": risk_assessment(lead),
}

ai_col_1, ai_col_2 = st.columns(2)

with ai_col_1:
    render_card("Account Summary", ai_sections["Account Summary"], "📋")
    render_card("Commercial Opportunity", ai_sections["Commercial Opportunity"], "💰")
    render_card("Partnership Hypothesis", ai_sections["Partnership Hypothesis"], "🤝")
    render_card("Suggested Stakeholder", ai_sections["Suggested Stakeholder"], "👤")

with ai_col_2:
    render_card("Why This Account Matters", ai_sections["Why This Account Matters"], "🎯")
    render_card("Expansion Hypothesis", ai_sections["Expansion Hypothesis"], "🌍")
    render_card("Recommended Outreach Strategy", ai_sections["Recommended Outreach Strategy"], "📨")
    render_card("Risk Assessment", ai_sections["Risk Assessment"], "⚠️")

ai_output_text = "\n\n".join([f"{key}:\n{value}" for key, value in ai_sections.items()])

os.makedirs("sequences", exist_ok=True)
ai_output_path = f"sequences/{safe_filename(lead['company'])}_ai_outreach_intelligence.txt"

with open(ai_output_path, "w", encoding="utf-8") as f:
    f.write(ai_output_text)

st.success(f"AI Outreach Intelligence saved to {ai_output_path}")

st.download_button(
    "⬇ Download AI Outreach Intelligence",
    ai_output_text,
    file_name=f"{safe_filename(lead['company'])}_ai_outreach_intelligence.txt",
    mime="text/plain",
)

st.divider()


st.subheader("📨 Sequence Generator")
st.caption("Generate a 4-step commercial follow-up sequence for post-proposal opportunities.")

if st.button("Generate Outreach Sequence"):
    sequence = local_sequence(lead, profile)

    tabs = st.tabs(list(sequence.keys()))

    for tab, (step, data) in zip(tabs, sequence.items()):
        with tab:
            render_card("Channel", data["channel"], "📡")
            if data.get("subject"):
                render_card("Subject", data["subject"], "✉️")
            render_card("Message", data["message"], "💬")

    output_text = sequence_to_text(lead["company"], sequence)

    os.makedirs("sequences", exist_ok=True)
    output_path = f"sequences/{safe_filename(lead['company'])}_sequence.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    st.success(f"Sequence saved to {output_path}")

    st.download_button(
        "⬇ Download Sequence",
        output_text,
        file_name=f"{safe_filename(lead['company'])}_sequence.txt",
        mime="text/plain",
    )
