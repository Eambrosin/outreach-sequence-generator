# Multilingual Outreach Sequence Generator

A Python tool that generates culturally-calibrated, language-specific
follow-up sequences for international B2B/B2G leads after a proposal
or FCO has been sent with no response.

## What it does

1. Reads a pipeline CSV of post-proposal leads.
2. For each lead, determines:
   - **Language** based on the country (Portuguese, Spanish, Italian, English)
   - **Channel** based on regional business culture (WhatsApp vs Email)
   - **Cultural tone** (e.g. relationship-first for LATAM/MENA, direct for Germany/Netherlands)
3. Calls the Claude API to generate a 4-message follow-up sequence:
   - **Day 1** — Soft check-in, confirm receipt, no pressure
   - **Day 3** — Add value, reinforce the proposal rationale
   - **Day 7** — Re-engagement question, gentle momentum
   - **Day 14** — Final touch, leave door open gracefully
4. Saves each sequence as a ready-to-use markdown file.

## Why the channel matters

| Region | Preferred channel | Notes |
|--------|------------------|-------|
| Brazil | WhatsApp | Standard for all business communication |
| Colombia / Mexico | WhatsApp | Relationship-driven, WhatsApp is primary |
| UAE / Saudi Arabia | Email → WhatsApp | Formal email Day 1; WhatsApp acceptable Day 3+ |
| Italy | WhatsApp | Widely used in Italian business |
| Germany / Netherlands | Email | Direct and structured; no WhatsApp for first contact |
| UK / USA | Email | Professional standard |

## How to run

```bash
pip install -r requirements.txt

# Without API key — shows cultural profile only
python outreach_generator.py --input pipeline.csv

# With API key — generates full sequences
export ANTHROPIC_API_KEY="your-key-here"
python outreach_generator.py --input pipeline.csv

# Single lead
python outreach_generator.py --lead "Gulf Trade Partners"
```

## Input format

Your `pipeline.csv` needs these columns:

| Column | Description |
|--------|-------------|
| `contact_name` | First and last name of the contact |
| `company` | Company name |
| `country` | Country (must match the supported list) |
| `industry` | Industry sector |
| `deal_type` | Type of proposal sent (FCO, Commercial Proposal, etc.) |
| `deal_value_usd` | Estimated deal value in USD |
| `proposal_sent_days_ago` | How many days ago the proposal was sent |
| `your_name` | Your name (used in the message signature) |

## Output

One markdown file per lead in the `/sequences` folder, containing:
- Lead summary table
- 4 ready-to-send messages with channel, subject line (if email), and full text
- All messages written in the correct language for that market

## Why I built this

After 10+ years in international B2B and B2G business development
across LATAM, MENA, and Europe, I noticed that most follow-up
sequences treat all leads the same. A follow-up that works for a
Brazilian contact on WhatsApp will land poorly with a Saudi buyer
expecting a formal email — and vice versa.

This tool encodes the cultural knowledge I use daily into a
replicable, AI-assisted workflow.

Companion project: [Lead Qualification Scorer](https://github.com/Eambrosin/lead-qualification-scorer)
— the scorer tells you *who* to contact first; this tool tells you *how and when*.
