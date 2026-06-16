"""
Multilingual Outreach Sequence Generator
-----------------------------------------
Takes a pipeline of leads (post-proposal / FCO stage) and generates
a 4-message follow-up sequence for each lead, using:

  - The correct language for the lead's country
  - The right channel (WhatsApp vs Email) based on regional culture
  - A tone calibrated to the business culture of that market
  - Timing: Day 1 / Day 3 / Day 7 / Day 14 after proposal sent

Output: one markdown file per lead saved in the /sequences folder,
        plus a summary printed to the terminal.

Usage:
    python outreach_generator.py --input pipeline.csv
    python outreach_generator.py --input pipeline.csv --lead "Gulf Trade Partners"
"""

import argparse
import os
import json
import re
import pandas as pd
import requests
from datetime import datetime

# ─────────────────────────────────────────────
# 1. COUNTRY → LANGUAGE + CHANNEL + TONE RULES
# ─────────────────────────────────────────────

COUNTRY_PROFILE = {
    # LATAM — Portuguese
    "Brazil":     {"language": "Portuguese", "channel": "WhatsApp",
                   "tone": "warm and relational; Brazilians value personal connection before business — be friendly, use first name, a touch of humor is welcome. Keep WhatsApp messages short (3-5 lines max)."},
    "Portugal":   {"language": "Portuguese", "channel": "WhatsApp",
                   "tone": "polite and slightly more formal than Brazilian Portuguese; respectful but approachable. Email for Day 1, WhatsApp from Day 3 onward."},

    # LATAM — Spanish
    "Colombia":   {"language": "Spanish", "channel": "WhatsApp",
                   "tone": "warm, respectful, relationship-first. Colombians appreciate courtesy and personal touch. Use 'usted' unless rapport is already established. WhatsApp widely used for business."},
    "Mexico":     {"language": "Spanish", "channel": "WhatsApp",
                   "tone": "friendly and indirect; Mexicans tend to avoid blunt pressure — frame urgency as opportunity, not deadline. WhatsApp is standard for business."},
    "Argentina":  {"language": "Spanish", "channel": "WhatsApp",
                   "tone": "direct and confident; Argentines appreciate intellectual engagement and dislike vague messaging. Can be slightly more assertive than other LATAM markets."},
    "Peru":       {"language": "Spanish", "channel": "WhatsApp",
                   "tone": "polite and formal initially; relationship building is important before pushing for a decision."},
    "Chile":      {"language": "Spanish", "channel": "Email",
                   "tone": "formal and structured; Chilean business culture is closer to European than to other LATAM markets. Email preferred for formal proposals."},
    "Uruguay":    {"language": "Spanish", "channel": "Email",
                   "tone": "professional and measured; low-pressure approach works best."},
    "Paraguay":   {"language": "Spanish", "channel": "WhatsApp",
                   "tone": "informal and relationship-driven; WhatsApp is standard."},

    # MENA — English with regional tone
    "UAE":          {"language": "English", "channel": "Email+WhatsApp",
                     "tone": "formal and respectful on Day 1 (Email); relationship-building tone, emphasize trust and long-term partnership. From Day 3, WhatsApp is acceptable. Reference the value of the partnership, not just the deal. Avoid pressure tactics."},
    "Saudi Arabia": {"language": "English", "channel": "Email",
                     "tone": "highly formal and respectful; address with title (Mr./Dr.) unless told otherwise. Emphasize mutual benefit, trust, and long-term vision. Avoid any mention of deadlines in early messages. Email preferred throughout."},
    "Egypt":        {"language": "English", "channel": "WhatsApp",
                     "tone": "warm and relationship-focused; Egyptians appreciate personal rapport. WhatsApp is widely used in business. Start formal, can soften tone after Day 1."},
    "Qatar":        {"language": "English", "channel": "Email",
                     "tone": "formal and concise; emphasize credibility and track record. Decision cycles are longer — patience is key."},
    "Kuwait":       {"language": "English", "channel": "Email",
                     "tone": "formal; relationship and trust-building before any commercial pressure."},
    "Jordan":       {"language": "English", "channel": "WhatsApp",
                     "tone": "warm but professional; WhatsApp common for business."},
    "Iraq":         {"language": "English", "channel": "WhatsApp",
                     "tone": "warm, relationship-first, patient. WhatsApp is the primary business channel."},
    "Bahrain":      {"language": "English", "channel": "Email",
                     "tone": "professional and concise; formal email preferred."},
    "Oman":         {"language": "English", "channel": "Email",
                     "tone": "formal, patient, relationship-oriented."},

    # EU
    "Italy":        {"language": "Italian", "channel": "WhatsApp",
                     "tone": "warm but professional; Italians value personal relationship and aesthetic quality of communication. WhatsApp is widely used for business in Italy. A touch of elegance in the language goes a long way."},
    "Spain":        {"language": "Spanish", "channel": "WhatsApp",
                     "tone": "friendly and direct; relationship-oriented but not as indirect as some LATAM markets. WhatsApp is standard for business in Spain."},
    "Germany":      {"language": "English", "channel": "Email",
                     "tone": "direct, formal, and structured. Germans value precision — be specific about what you are following up on and what next step you propose. No small talk. Email strongly preferred."},
    "Netherlands":  {"language": "English", "channel": "Email",
                     "tone": "direct and efficient; similar to German but slightly more informal. Get to the point quickly."},
    "France":       {"language": "English", "channel": "Email",
                     "tone": "formal and intellectually engaging; French professionals appreciate substance over hype. Email preferred."},
    "UK":           {"language": "English", "channel": "Email",
                     "tone": "professional, understated, and polite. British communication tends to be indirect about pressure — suggest rather than demand. Email preferred."},
    "Austria":      {"language": "English", "channel": "Email",
                     "tone": "formal and structured, similar to German. Email preferred."},
    "Switzerland":  {"language": "English", "channel": "Email",
                     "tone": "precise, formal, and neutral. Email strongly preferred."},
    "Portugal":     {"language": "Portuguese", "channel": "Email",
                     "tone": "polite and formal; slightly more reserved than Brazilian Portuguese."},
}

DEFAULT_PROFILE = {
    "language": "English",
    "channel":  "Email",
    "tone":     "professional and concise; adapt to local norms if known.",
}

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


# ─────────────────────────────────────────────
# 2. CLAUDE API CALL
# ─────────────────────────────────────────────

def generate_sequence(lead: dict, profile: dict):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    channel_note = {
        "WhatsApp":       "WhatsApp messages: short (3–6 lines max), no formal subject line, conversational but professional. Start with a friendly greeting.",
        "Email":          "Email format: include Subject line, formal salutation, 2–4 short paragraphs, professional sign-off.",
        "Email+WhatsApp": "Day 1: Email format with Subject line. Days 3, 7, 14: WhatsApp format — short (3–6 lines), no subject line.",
    }.get(profile["channel"], "Email format.")

    prompt = f"""You are a senior international business development consultant helping Eduardo Ambrosin follow up with a lead after sending a proposal/FCO that has not yet been answered.

LEAD PROFILE:
- Contact: {lead['contact_name']}
- Company: {lead['company']}
- Country: {lead['country']}
- Industry: {lead['industry']}
- Deal type: {lead['deal_type']}
- Deal value: USD {int(lead['deal_value_usd']):,}
- Proposal sent: {lead['proposal_sent_days_ago']} days ago
- Sender name: {lead['your_name']}

COMMUNICATION RULES:
- Language: {profile['language']}
- Channel: {profile['channel']}
- {channel_note}
- Cultural tone: {profile['tone']}

SEQUENCE STRATEGY (post-proposal / FCO stage, no response yet):
- Day 1: Soft, friendly check-in. Confirm receipt, offer to answer questions. No pressure.
- Day 3: Add value — share a brief insight relevant to their industry or market. Reinforce why the proposal makes sense for them.
- Day 7: Ask a specific, easy-to-answer question to re-engage. Create gentle momentum.
- Day 14: Final follow-up — leave the door open gracefully. Offer to adjust the proposal if needed. No hard sell.

Generate exactly 4 messages. Respond ONLY with valid JSON, no markdown, no preamble, in this exact format:
{{
  "day_1": {{"label": "Day 1 — Soft Check-in", "channel": "...", "subject": "...", "message": "..."}},
  "day_3": {{"label": "Day 3 — Value Add", "channel": "...", "subject": "...", "message": "..."}},
  "day_7": {{"label": "Day 7 — Re-engagement", "channel": "...", "subject": "...", "message": "..."}},
  "day_14": {{"label": "Day 14 — Final Touch", "channel": "...", "subject": "...", "message": "..."}}
}}

For WhatsApp messages, leave "subject" as empty string "".
Write ALL messages in {profile['language']}.
"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      ANTHROPIC_MODEL,
                "max_tokens": 2000,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=45,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"]
        # strip possible markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(clean)
    except Exception as exc:
        print(f"  [AI] Error for {lead['company']}: {exc}")
        return None


# ─────────────────────────────────────────────
# 3. MARKDOWN OUTPUT
# ─────────────────────────────────────────────

def save_markdown(lead: dict, profile: dict, sequence: dict, output_dir: str):
    safe_name = re.sub(r"[^\w\-]", "_", lead["company"])
    filepath   = os.path.join(output_dir, f"{safe_name}_sequence.md")

    lines = [
        f"# Follow-up Sequence — {lead['company']}",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Contact | {lead['contact_name']} |",
        f"| Country | {lead['country']} |",
        f"| Industry | {lead['industry']} |",
        f"| Deal | {lead['deal_type']} — USD {int(lead['deal_value_usd']):,} |",
        f"| Proposal sent | {lead['proposal_sent_days_ago']} days ago |",
        f"| Language | {profile['language']} |",
        f"| Channel | {profile['channel']} |",
        f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M')} |",
        f"",
        f"---",
        f"",
    ]

    for key in ["day_1", "day_3", "day_7", "day_14"]:
        msg = sequence.get(key, {})
        lines.append(f"## {msg.get('label', key.upper())}")
        lines.append(f"**Channel:** {msg.get('channel', profile['channel'])}")
        if msg.get("subject"):
            lines.append(f"**Subject:** {msg['subject']}")
        lines.append(f"")
        lines.append(msg.get("message", ""))
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


# ─────────────────────────────────────────────
# 4. MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Multilingual outreach sequence generator")
    parser.add_argument("--input",  default="pipeline.csv",   help="CSV file with leads")
    parser.add_argument("--lead",   default=None,             help="Filter by company name (optional)")
    parser.add_argument("--output", default="sequences",      help="Output folder for markdown files")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    df = pd.read_csv(args.input)

    if args.lead:
        df = df[df["company"].str.lower().str.contains(args.lead.lower())]
        if df.empty:
            print(f"No lead found matching '{args.lead}'")
            return

    has_api = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not has_api:
        print("\n[Info] ANTHROPIC_API_KEY not set.")
        print("       The script will show the cultural profile for each lead")
        print("       but skip AI message generation.")
        print("       export ANTHROPIC_API_KEY='your-key' to generate sequences.\n")

    print(f"\n{'='*60}")
    print(f"  OUTREACH SEQUENCE GENERATOR — {len(df)} lead(s)")
    print(f"{'='*60}\n")

    for _, row in df.iterrows():
        lead    = row.to_dict()
        profile = COUNTRY_PROFILE.get(lead["country"], DEFAULT_PROFILE)

        print(f"→ {lead['company']} ({lead['country']})")
        print(f"  Contact : {lead['contact_name']}")
        print(f"  Deal    : {lead['deal_type']} — USD {int(lead['deal_value_usd']):,}")
        print(f"  Proposal: {lead['proposal_sent_days_ago']} days ago")
        print(f"  Language: {profile['language']}  |  Channel: {profile['channel']}")

        if has_api:
            print(f"  Generating sequence via Claude API...")
            sequence = generate_sequence(lead, profile)
            if sequence:
                path = save_markdown(lead, profile, sequence, args.output)
                print(f"  ✓ Saved → {path}")

                # Print Day 1 preview in terminal
                d1 = sequence.get("day_1", {})
                print(f"\n  ── Day 1 preview ──")
                if d1.get("subject"):
                    print(f"  Subject: {d1['subject']}")
                preview = d1.get("message", "")[:300]
                for line in preview.split("\n"):
                    print(f"  {line}")
                if len(d1.get("message","")) > 300:
                    print(f"  [... see full file]")
            else:
                print(f"  ✗ Generation failed — check your API key and connection.")
        else:
            print(f"  Cultural tone: {profile['tone'][:80]}...")

        print()

    if has_api:
        print(f"All sequences saved to: ./{args.output}/")
    print("Done.\n")


if __name__ == "__main__":
    main()
