"""
Adaptive Outreach Intelligence Engine
--------------------------------------

Supports two operating modes:

1. Standard Outreach Mode
   For traditional post-proposal / FCO pipelines.

2. Commercial Intelligence Mode
   For pipelines exported from the Lead Qualification &
   Revenue Prioritization Platform.

The engine can use:

- Lead score
- Priority tier
- Engagement signal
- Recommended commercial action
- Score rationale
- Proposal age
- Deal value
- Country
- Language
- Preferred communication channel

The deterministic strategy engine decides cadence, priority and
commercial objective.

AI may generate the messages, but it does not determine the
underlying commercial priority.
"""

import argparse
import json
import os
import re
from datetime import datetime

import pandas as pd
import requests


# ----------------------------------------------------------------------
# 1. COUNTRY / LANGUAGE / CHANNEL PROFILES
# ----------------------------------------------------------------------

COUNTRY_PROFILE = {

    "Brazil": {
        "language": "Portuguese",
        "channel": "WhatsApp",
        "tone": "warm, concise and professional",
    },

    "Portugal": {
        "language": "Portuguese",
        "channel": "Email",
        "tone": "polite, professional and slightly formal",
    },

    "Colombia": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "warm, respectful and professional",
    },

    "Mexico": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "friendly, consultative and low-pressure",
    },

    "Argentina": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "direct, confident and commercially substantive",
    },

    "Peru": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "polite and consultative",
    },

    "Chile": {
        "language": "Spanish",
        "channel": "Email",
        "tone": "structured, concise and professional",
    },

    "Uruguay": {
        "language": "Spanish",
        "channel": "Email",
        "tone": "professional and measured",
    },

    "Paraguay": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "friendly and concise",
    },

    "Spain": {
        "language": "Spanish",
        "channel": "WhatsApp",
        "tone": "friendly, direct and professional",
    },

    "UAE": {
        "language": "English",
        "channel": "Email+WhatsApp",
        "tone": "formal, respectful and partnership-oriented",
    },

    "United Arab Emirates": {
        "language": "English",
        "channel": "Email+WhatsApp",
        "tone": "formal, respectful and partnership-oriented",
    },

    "Saudi Arabia": {
        "language": "English",
        "channel": "Email",
        "tone": "formal, respectful and relationship-oriented",
    },

    "Egypt": {
        "language": "English",
        "channel": "WhatsApp",
        "tone": "warm and professional",
    },

    "Qatar": {
        "language": "English",
        "channel": "Email",
        "tone": "formal, concise and credibility-focused",
    },

    "Kuwait": {
        "language": "English",
        "channel": "Email",
        "tone": "formal and patient",
    },

    "Jordan": {
        "language": "English",
        "channel": "WhatsApp",
        "tone": "warm and professional",
    },

    "Iraq": {
        "language": "English",
        "channel": "WhatsApp",
        "tone": "professional and relationship-oriented",
    },

    "Bahrain": {
        "language": "English",
        "channel": "Email",
        "tone": "professional and concise",
    },

    "Oman": {
        "language": "English",
        "channel": "Email",
        "tone": "formal and patient",
    },

    "Italy": {
        "language": "Italian",
        "channel": "WhatsApp",
        "tone": "warm, polished and professional",
    },

    "France": {
        "language": "French",
        "channel": "Email",
        "tone": "formal, substantive and concise",
    },

    "Germany": {
        "language": "German",
        "channel": "Email",
        "tone": "direct, structured and precise",
    },

    "Netherlands": {
        "language": "English",
        "channel": "Email",
        "tone": "direct and efficient",
    },

    "UK": {
        "language": "English",
        "channel": "Email",
        "tone": "professional, understated and polite",
    },

    "United Kingdom": {
        "language": "English",
        "channel": "Email",
        "tone": "professional, understated and polite",
    },

    "Austria": {
        "language": "German",
        "channel": "Email",
        "tone": "formal and structured",
    },

    "Switzerland": {
        "language": "English",
        "channel": "Email",
        "tone": "precise, formal and neutral",
    },

    "United States": {
        "language": "English",
        "channel": "Email",
        "tone": "direct, concise and outcome-oriented",
    },

    "Singapore": {
        "language": "English",
        "channel": "Email",
        "tone": "concise and commercially focused",
    },

    "South Africa": {
        "language": "English",
        "channel": "Email",
        "tone": "professional and consultative",
    },
}


DEFAULT_PROFILE = {
    "language": "English",
    "channel": "Email",
    "tone": "professional, concise and consultative",
}


ANTHROPIC_MODEL = os.environ.get(
    "ANTHROPIC_MODEL",
    "claude-sonnet-4-6",
)


# ----------------------------------------------------------------------
# 2. DATA NORMALIZATION
# ----------------------------------------------------------------------

def first_value(
    row,
    keys,
    default="",
):

    for key in keys:

        try:
            value = row.get(
                key,
                None,
            )

        except AttributeError:
            value = None

        if value is None:
            continue

        if (
            isinstance(
                value,
                float,
            )
            and pd.isna(
                value
            )
        ):
            continue

        if str(
            value
        ).strip():
            return value

    return default


def safe_float(
    value,
    default=0.0,
):

    try:

        if value is None:
            return float(
                default
            )

        if (
            isinstance(
                value,
                float,
            )
            and pd.isna(
                value
            )
        ):
            return float(
                default
            )

        return float(
            value
        )

    except Exception:

        return float(
            default
        )


def normalize_lead(
    row,
):
    """
    Makes the engine compatible with both:

    Original outreach pipeline:
        company
        deal_value_usd
        proposal_sent_days_ago

    Lead Qualification export:
        company_name
        estimated_deal_value_usd
        score
        tier
        engagement_signal
        recommended_action
    """

    proposal_raw = first_value(
        row,
        [
            "proposal_sent_days_ago",
        ],
        None,
    )

    if proposal_raw is None:
        proposal_days = None

    else:
        proposal_days = int(
            safe_float(
                proposal_raw,
                0,
            )
        )

    score_raw = first_value(
        row,
        [
            "score",
        ],
        None,
    )

    score = (
        None
        if score_raw is None
        else safe_float(
            score_raw,
            0,
        )
    )

    lead = {

        "contact_name": str(
            first_value(
                row,
                [
                    "contact_name",
                    "contact",
                ],
                "",
            )
        ).strip(),

        "company": str(
            first_value(
                row,
                [
                    "company",
                    "company_name",
                ],
                "Unknown Company",
            )
        ).strip(),

        "country": str(
            first_value(
                row,
                [
                    "country",
                ],
                "",
            )
        ).strip(),

        "region": str(
            first_value(
                row,
                [
                    "region",
                ],
                "",
            )
        ).strip(),

        "industry": str(
            first_value(
                row,
                [
                    "industry",
                ],
                "Unknown Industry",
            )
        ).strip(),

        "company_size": first_value(
            row,
            [
                "company_size",
            ],
            "",
        ),

        "deal_type": str(
            first_value(
                row,
                [
                    "deal_type",
                ],
                "Commercial Opportunity",
            )
        ).strip(),

        "deal_value_usd": safe_float(
            first_value(
                row,
                [
                    "deal_value_usd",
                    "estimated_deal_value_usd",
                ],
                0,
            )
        ),

        "proposal_sent_days_ago": (
            proposal_days
        ),

        "your_name": str(
            first_value(
                row,
                [
                    "your_name",
                ],
                "Eduardo Ambrosin",
            )
        ).strip(),

        "engagement_signal": str(
            first_value(
                row,
                [
                    "engagement_signal",
                ],
                "",
            )
        ).strip().lower(),

        "score": score,

        "tier": str(
            first_value(
                row,
                [
                    "tier",
                ],
                "",
            )
        ).strip().upper(),

        "recommended_action": str(
            first_value(
                row,
                [
                    "recommended_action",
                ],
                "",
            )
        ).strip(),

        "score_rationale": str(
            first_value(
                row,
                [
                    "score_rationale",
                ],
                "",
            )
        ).strip(),
    }

    lead[
        "commercial_intelligence_mode"
    ] = bool(
        lead["tier"]
        or lead["score"] is not None
        or lead[
            "recommended_action"
        ]
        or lead[
            "score_rationale"
        ]
    )

    lead[
        "outreach_stage"
    ] = (
        "post_proposal"
        if proposal_days
        is not None
        else "prospecting"
    )

    return lead


# ----------------------------------------------------------------------
# 3. COMMERCIAL PRIORITY
# ----------------------------------------------------------------------

def commercial_priority(
    lead,
):

    tier = lead.get(
        "tier",
        "",
    )

    score = lead.get(
        "score",
        None,
    )

    engagement = lead.get(
        "engagement_signal",
        "",
    )

    proposal_days = lead.get(
        "proposal_sent_days_ago",
        None,
    )

    deal_value = lead.get(
        "deal_value_usd",
        0,
    )

    if tier == "A":
        return "High"

    if tier == "B":
        return "Medium"

    if tier == "C":
        return "Low"

    if score is not None:

        if score >= 75:
            return "High"

        if score >= 50:
            return "Medium"

        return "Low"

    if (
        proposal_days
        is not None
        and proposal_days >= 10
    ):
        return "High"

    if (
        engagement
        == "hot"
    ):
        return "High"

    if deal_value >= 500000:
        return "High"

    if deal_value >= 150000:
        return "Medium"

    return "Low"


# ----------------------------------------------------------------------
# 4. ADAPTIVE OUTREACH STRATEGY
# ----------------------------------------------------------------------

def build_outreach_strategy(
    lead,
    profile=None,
):

    if profile is None:

        profile = (
            COUNTRY_PROFILE.get(
                lead.get(
                    "country",
                    "",
                ),
                DEFAULT_PROFILE,
            )
        )

    priority = commercial_priority(
        lead
    )

    engagement = lead.get(
        "engagement_signal",
        "",
    )

    stage = lead.get(
        "outreach_stage",
        "prospecting",
    )

    proposal_days = lead.get(
        "proposal_sent_days_ago",
        None,
    )

    # Standard cadence
    cadence_days = [
        0,
        3,
        7,
        14,
    ]

    intensity = "balanced"

    objective = (
        "Create a relevant commercial conversation "
        "and validate business fit."
    )

    # High priority
    if priority == "High":

        cadence_days = [
            0,
            2,
            5,
            10,
        ]

        intensity = (
            "high-touch"
        )

        objective = (
            "Create near-term engagement, validate "
            "decision context and move toward a concrete next step."
        )

    # Low priority
    elif priority == "Low":

        cadence_days = [
            0,
            7,
            21,
            35,
        ]

        intensity = (
            "low-touch"
        )

        objective = (
            "Validate relevance without over-investing "
            "commercial resources."
        )

    # Engagement override
    if engagement == "hot":

        cadence_days = [
            0,
            2,
            5,
            10,
        ]

        intensity = (
            "high-touch"
        )

    elif (
        engagement == "cold"
        and priority != "High"
    ):

        cadence_days = [
            0,
            7,
            21,
            35,
        ]

        intensity = (
            "low-touch"
        )

    # Aged proposal
    if (
        stage == "post_proposal"
        and proposal_days
        is not None
        and proposal_days >= 10
    ):

        objective = (
            "Clarify proposal status, surface blockers "
            "and obtain a clear next step while preserving "
            "the commercial relationship."
        )

    recommended_action = (
        lead.get(
            "recommended_action",
            "",
        )
    )

    if recommended_action:

        objective += (
            " Internal recommendation: "
            + recommended_action
            + "."
        )

    touches = [

        {
            "offset_days": (
                cadence_days[0]
            ),
            "name": (
                "Relevant Opening"
            ),
            "goal": (
                "Establish relevance and make "
                "the next response easy."
            ),
        },

        {
            "offset_days": (
                cadence_days[1]
            ),
            "name": (
                "Value Reinforcement"
            ),
            "goal": (
                "Add a useful commercial angle "
                "without inventing company facts."
            ),
        },

        {
            "offset_days": (
                cadence_days[2]
            ),
            "name": (
                "Specific Re-engagement"
            ),
            "goal": (
                "Ask one concrete question that "
                "clarifies fit, timing or decision process."
            ),
        },

        {
            "offset_days": (
                cadence_days[3]
            ),
            "name": (
                "Close the Loop"
            ),
            "goal": (
                "Leave the door open professionally "
                "and create a future re-entry point."
            ),
        },
    ]

    return {

        "mode": (
            "Commercial Intelligence"
            if lead.get(
                "commercial_intelligence_mode",
                False,
            )
            else "Standard Outreach"
        ),

        "stage": stage,

        "priority": priority,

        "tier": (
            lead.get(
                "tier",
                "",
            )
            or "N/A"
        ),

        "engagement_signal": (
            engagement
            or "Not provided"
        ),

        "intensity": (
            intensity
        ),

        "language": (
            profile[
                "language"
            ]
        ),

        "primary_channel": (
            profile[
                "channel"
            ]
        ),

        "tone": (
            profile[
                "tone"
            ]
        ),

        "commercial_objective": (
            objective
        ),

        "cadence_days": (
            cadence_days
        ),

        "touches": (
            touches
        ),
    }


# ----------------------------------------------------------------------
# 5. CHANNEL STRATEGY
# ----------------------------------------------------------------------

def channel_for_touch(
    profile,
    touch_number,
):

    channel = profile[
        "channel"
    ]

    if channel == "Email+WhatsApp":

        if touch_number == 1:
            return "Email"

        return "WhatsApp"

    return channel


def channel_note(
    channel,
):

    if channel == "WhatsApp":

        return (
            "Keep it short, conversational and professional. "
            "No subject line. Aim for 3 to 6 short lines."
        )

    return (
        "Use a concise subject line, professional salutation, "
        "short paragraphs and a clear low-pressure CTA."
    )


# ----------------------------------------------------------------------
# 6. INTERNAL COMMERCIAL CONTEXT
# ----------------------------------------------------------------------

def internal_context(
    lead,
    strategy,
):

    context = {

        "mode": (
            strategy[
                "mode"
            ]
        ),

        "stage": (
            strategy[
                "stage"
            ]
        ),

        "priority": (
            strategy[
                "priority"
            ]
        ),

        "score": (
            lead.get(
                "score",
                None,
            )
        ),

        "tier": (
            lead.get(
                "tier",
                "",
            )
        ),

        "engagement_signal": (
            lead.get(
                "engagement_signal",
                "",
            )
        ),

        "recommended_action": (
            lead.get(
                "recommended_action",
                "",
            )
        ),

        "score_rationale": (
            lead.get(
                "score_rationale",
                "",
            )
        ),

        "commercial_objective": (
            strategy[
                "commercial_objective"
            ]
        ),
    }

    return json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# ----------------------------------------------------------------------
# 7. AI SEQUENCE GENERATION
# ----------------------------------------------------------------------

def generate_sequence(
    lead: dict,
    profile: dict,
):

    # Normalize while keeping compatibility
    lead = normalize_lead(
        lead
    )

    strategy = (
        build_outreach_strategy(
            lead,
            profile,
        )
    )

    api_key = (
        os.environ.get(
            "ANTHROPIC_API_KEY"
        )
    )

    if not api_key:

        return (
            generate_local_sequence(
                lead,
                profile,
                strategy,
            )
        )

    proposal_age = (
        f"{lead['proposal_sent_days_ago']} days ago"
        if lead[
            "proposal_sent_days_ago"
        ]
        is not None
        else "Not applicable"
    )

    touches = []

    for index, touch in enumerate(
        strategy[
            "touches"
        ],
        start=1,
    ):

        channel = (
            channel_for_touch(
                profile,
                index,
            )
        )

        touches.append(
            f"""
Touch {index}
Timing: Day +{touch['offset_days']}
Objective: {touch['name']}
Goal: {touch['goal']}
Channel: {channel}
Format: {channel_note(channel)}
""".strip()
        )

    prompt = f"""
You are a senior international Business Development and GTM professional.

Create a four-touch commercial outreach sequence.

ACCOUNT DATA

Contact:
{lead['contact_name'] or 'Not provided'}

Company:
{lead['company']}

Country:
{lead['country']}

Region:
{lead['region'] or 'Not provided'}

Industry:
{lead['industry']}

Deal Type:
{lead['deal_type']}

Estimated Deal Value:
USD {int(lead['deal_value_usd']):,}

Proposal Age:
{proposal_age}

Sender:
{lead['your_name']}


COMMUNICATION PROFILE

Language:
{profile['language']}

Default Channel:
{profile['channel']}

Tone:
{profile['tone']}


INTERNAL COMMERCIAL INTELLIGENCE

{internal_context(lead, strategy)}


IMPORTANT RULES

Internal commercial intelligence is used only to guide strategy.

Never expose to the prospect:

- lead score
- tier
- internal priority
- score rationale
- scoring methodology

Do not invent:

- company projects
- budgets
- decision makers
- pain points
- expansion plans
- growth initiatives
- market research

If something is not confirmed by the supplied data,
frame it as a question or hypothesis.


OUTREACH STRATEGY

Mode:
{strategy['mode']}

Intensity:
{strategy['intensity']}

Commercial Objective:
{strategy['commercial_objective']}


TOUCH PLAN

{chr(10).join(touches)}


Return ONLY valid JSON.

Keep these JSON keys exactly:

day_1
day_3
day_7
day_14

Even if the adaptive timing is different.

Required structure:

{{
    "day_1": {{
        "label": "Touch 1 — ...",
        "timing": "Day +0",
        "channel": "...",
        "subject": "...",
        "message": "..."
    }},
    "day_3": {{
        "label": "Touch 2 — ...",
        "timing": "Day +...",
        "channel": "...",
        "subject": "...",
        "message": "..."
    }},
    "day_7": {{
        "label": "Touch 3 — ...",
        "timing": "Day +...",
        "channel": "...",
        "subject": "...",
        "message": "..."
    }},
    "day_14": {{
        "label": "Touch 4 — ...",
        "timing": "Day +...",
        "channel": "...",
        "subject": "...",
        "message": "..."
    }}
}}

For WhatsApp, subject must be "".

Write prospect-facing messages in:

{profile['language']}
""".strip()

    try:

        response = requests.post(

            "https://api.anthropic.com/v1/messages",

            headers={

                "x-api-key": (
                    api_key
                ),

                "anthropic-version": (
                    "2023-06-01"
                ),

                "content-type": (
                    "application/json"
                ),
            },

            json={

                "model": (
                    ANTHROPIC_MODEL
                ),

                "max_tokens": (
                    2400
                ),

                "messages": [

                    {
                        "role": "user",
                        "content": prompt,
                    }

                ],
            },

            timeout=45,
        )

        response.raise_for_status()

        content_blocks = (
            response.json().get(
                "content",
                [],
            )
        )

        raw = next(

            (
                block.get(
                    "text"
                )

                for block
                in content_blocks

                if block.get(
                    "type"
                )
                == "text"
            ),

            None,
        )

        if not raw:

            raise ValueError(
                "No text returned by API."
            )

        clean = re.sub(
            r"```(?:json)?|```",
            "",
            raw,
        ).strip()

        sequence = json.loads(
            clean
        )

        return apply_strategy_metadata(
            sequence,
            strategy,
            profile,
        )

    except Exception as exc:

        print(
            f"[AI] Generation failed for "
            f"{lead['company']}: {exc}"
        )

        return (
            generate_local_sequence(
                lead,
                profile,
                strategy,
            )
        )


# ----------------------------------------------------------------------
# 8. STRATEGY METADATA
# ----------------------------------------------------------------------

def apply_strategy_metadata(
    sequence,
    strategy,
    profile,
):

    keys = [
        "day_1",
        "day_3",
        "day_7",
        "day_14",
    ]

    for index, key in enumerate(
        keys,
        start=1,
    ):

        touch = (
            strategy[
                "touches"
            ][
                index - 1
            ]
        )

        message = (
            sequence.get(
                key,
                {},
            )
        )

        message[
            "label"
        ] = (
            f"Touch {index} — "
            f"{touch['name']}"
        )

        message[
            "timing"
        ] = (
            f"Day +"
            f"{touch['offset_days']}"
        )

        message[
            "channel"
        ] = (
            channel_for_touch(
                profile,
                index,
            )
        )

        if (
            message[
                "channel"
            ]
            == "WhatsApp"
        ):

            message[
                "subject"
            ] = ""

        sequence[
            key
        ] = message

    return sequence


# ----------------------------------------------------------------------
# 9. LOCAL FALLBACK
# ----------------------------------------------------------------------

def local_message(
    language,
    lead,
    touch_number,
):

    company = (
        lead[
            "company"
        ]
    )

    sender = (
        lead[
            "your_name"
        ]
    )

    contact = (
        lead[
            "contact_name"
        ]
    )

    stage = (
        lead[
            "outreach_stage"
        ]
    )

    name = (
        contact
        if contact
        else ""
    )

    if language == "Portuguese":

        greeting = (
            f"Olá {name},"
            if name
            else "Olá,"
        )

        templates = {

            1: (
                f"{greeting}\n\n"
                f"Gostaria de entender se faz sentido conversarmos "
                f"sobre possíveis prioridades comerciais, parcerias "
                f"ou oportunidades relacionadas à {company}.\n\n"
                f"Se for relevante, posso adaptar a conversa "
                f"ao momento atual da sua equipe.\n\n"
                f"Abraço,\n{sender}"
            ),

            2: (
                f"{greeting}\n\n"
                f"Retomo rapidamente o contato. "
                f"Uma conversa inicial pode ajudar a entender "
                f"onde existe prioridade comercial real e onde "
                f"poderíamos gerar valor.\n\n"
                f"Existe algum tema de crescimento, parceria "
                f"ou expansão em avaliação?\n\n"
                f"{sender}"
            ),

            3: (
                f"{greeting}\n\n"
                f"Uma pergunta objetiva: faria sentido uma breve "
                f"conversa para validar se existe aderência comercial "
                f"entre nossas áreas de atuação?\n\n"
                f"{sender}"
            ),

            4: (
                f"{greeting}\n\n"
                f"Faço este último contato por agora para não insistir. "
                f"Se o tema não for prioridade neste momento, "
                f"sem problema. Fico à disposição para retomarmos "
                f"quando fizer sentido.\n\n"
                f"Abraço,\n{sender}"
            ),
        }

    elif language == "Spanish":

        greeting = (
            f"Hola {name},"
            if name
            else "Hola,"
        )

        templates = {

            1: (
                f"{greeting}\n\n"
                f"Quisiera entender si tendría sentido conversar "
                f"sobre prioridades comerciales, alianzas o posibles "
                f"oportunidades relacionadas con {company}.\n\n"
                f"Si es relevante, puedo adaptar la conversación "
                f"al momento de su equipo.\n\n"
                f"Saludos,\n{sender}"
            ),

            2: (
                f"{greeting}\n\n"
                f"Retomo brevemente el contacto. "
                f"Una conversación inicial puede ayudar a identificar "
                f"dónde existe una prioridad comercial real.\n\n"
                f"¿Hay temas de crecimiento, alianzas o expansión "
                f"que estén evaluando actualmente?\n\n"
                f"{sender}"
            ),

            3: (
                f"{greeting}\n\n"
                f"Una pregunta concreta: ¿tendría sentido una breve "
                f"conversación para validar si existe encaje comercial?\n\n"
                f"{sender}"
            ),

            4: (
                f"{greeting}\n\n"
                f"Hago este último seguimiento por ahora para no insistir. "
                f"Si no es una prioridad en este momento, no hay problema. "
                f"Quedo disponible para retomarlo más adelante.\n\n"
                f"Saludos,\n{sender}"
            ),
        }

    elif language == "Italian":

        greeting = (
            f"Buongiorno {name},"
            if name
            else "Buongiorno,"
        )

        templates = {

            1: (
                f"{greeting}\n\n"
                f"Mi farebbe piacere capire se possa avere senso "
                f"confrontarci su priorità commerciali, partnership "
                f"o opportunità relative a {company}.\n\n"
                f"Se il tema è rilevante, posso adattare la conversazione "
                f"alle vostre priorità attuali.\n\n"
                f"Cordiali saluti,\n{sender}"
            ),

            2: (
                f"{greeting}\n\n"
                f"Riprendo brevemente il contatto. "
                f"Una prima conversazione potrebbe aiutarci a capire "
                f"dove esista una reale priorità commerciale.\n\n"
                f"State valutando temi legati a crescita, partnership "
                f"o nuovi mercati?\n\n"
                f"{sender}"
            ),

            3: (
                f"{greeting}\n\n"
                f"Una domanda molto semplice: avrebbe senso una breve "
                f"conversazione per verificare se esiste un possibile "
                f"allineamento commerciale?\n\n"
                f"{sender}"
            ),

            4: (
                f"{greeting}\n\n"
                f"Le scrivo un'ultima volta per ora, senza voler insistere. "
                f"Se il tema non è prioritario in questo momento, "
                f"nessun problema. Rimango disponibile per riprenderlo "
                f"in futuro.\n\n"
                f"Cordiali saluti,\n{sender}"
            ),
        }

    else:

        greeting = (
            f"Hello {name},"
            if name
            else "Hello,"
        )

        templates = {

            1: (
                f"{greeting}\n\n"
                f"I wanted to understand whether a conversation around "
                f"commercial priorities, partnerships or business development "
                f"could be relevant for {company}.\n\n"
                f"If so, I would be happy to adapt the discussion "
                f"to your current priorities.\n\n"
                f"Best,\n{sender}"
            ),

            2: (
                f"{greeting}\n\n"
                f"A quick follow-up. An initial conversation could help "
                f"determine whether there is a genuine commercial priority "
                f"worth exploring.\n\n"
                f"Are growth, partnerships or market development areas "
                f"you are currently evaluating?\n\n"
                f"Best,\n{sender}"
            ),

            3: (
                f"{greeting}\n\n"
                f"One simple question: would a short conversation make sense "
                f"to validate whether there is a relevant commercial fit?\n\n"
                f"Best,\n{sender}"
            ),

            4: (
                f"{greeting}\n\n"
                f"I will close the loop for now so I do not over-follow up. "
                f"If this is not a priority at the moment, no problem at all. "
                f"I would be happy to reconnect when the timing is more relevant.\n\n"
                f"Best,\n{sender}"
            ),
        }

    # Post-proposal first touch
    if (
        stage == "post_proposal"
        and touch_number == 1
    ):

        if language == "Portuguese":

            return (
                f"{greeting}\n\n"
                f"Queria apenas confirmar se você conseguiu receber "
                f"e revisar a proposta referente a {company}. "
                f"Se houver algum ponto que precise de esclarecimento "
                f"ou ajuste, fico à disposição.\n\n"
                f"Abraço,\n{sender}"
            )

        if language == "Spanish":

            return (
                f"{greeting}\n\n"
                f"Quería confirmar si pudo recibir y revisar "
                f"la propuesta relacionada con {company}. "
                f"Si hay algún punto que requiera aclaración "
                f"o ajuste, quedo a disposición.\n\n"
                f"Saludos,\n{sender}"
            )

        if language == "Italian":

            return (
                f"{greeting}\n\n"
                f"Volevo semplicemente verificare che abbia ricevuto "
                f"e potuto esaminare la proposta relativa a {company}. "
                f"Se ci sono punti da chiarire o adattare, "
                f"resto a disposizione.\n\n"
                f"Cordiali saluti,\n{sender}"
            )

        return (
            f"{greeting}\n\n"
            f"I wanted to confirm that you received and had a chance "
            f"to review the proposal regarding {company}. "
            f"If there are any points that need clarification or adjustment, "
            f"I am happy to address them.\n\n"
            f"Best,\n{sender}"
        )

    return templates[
        touch_number
    ]


def generate_local_sequence(
    lead,
    profile,
    strategy=None,
):

    if strategy is None:

        strategy = (
            build_outreach_strategy(
                lead,
                profile,
            )
        )

    sequence = {}

    keys = [
        "day_1",
        "day_3",
        "day_7",
        "day_14",
    ]

    for index, key in enumerate(
        keys,
        start=1,
    ):

        touch = (
            strategy[
                "touches"
            ][
                index - 1
            ]
        )

        channel = (
            channel_for_touch(
                profile,
                index,
            )
        )

        subject = ""

        if channel == "Email":

            subject = (
                f"Commercial conversation — "
                f"{lead['company']}"
            )

        sequence[
            key
        ] = {

            "label": (
                f"Touch {index} — "
                f"{touch['name']}"
            ),

            "timing": (
                f"Day +"
                f"{touch['offset_days']}"
            ),

            "channel": channel,

            "subject": subject,

            "message": (
                local_message(
                    profile[
                        "language"
                    ],
                    lead,
                    index,
                )
            ),
        }

    return sequence


# ----------------------------------------------------------------------
# 10. MARKDOWN EXPORT
# ----------------------------------------------------------------------

def save_markdown(
    lead: dict,
    profile: dict,
    sequence: dict,
    output_dir: str,
):

    lead = normalize_lead(
        lead
    )

    strategy = (
        build_outreach_strategy(
            lead,
            profile,
        )
    )

    safe_name = re.sub(
        r"[^\w\-]",
        "_",
        lead[
            "company"
        ],
    )

    filepath = os.path.join(
        output_dir,
        f"{safe_name}_sequence.md",
    )

    proposal_age = (
        f"{lead['proposal_sent_days_ago']} days"
        if lead[
            "proposal_sent_days_ago"
        ]
        is not None
        else "N/A"
    )

    score_display = (
        f"{lead['score']:.1f}"
        if lead[
            "score"
        ]
        is not None
        else "N/A"
    )

    lines = [

        f"# Outreach Sequence — {lead['company']}",

        "",

        "| Field | Value |",

        "|---|---|",

        f"| Contact | {lead['contact_name'] or 'Not provided'} |",

        f"| Country | {lead['country'] or 'Not provided'} |",

        f"| Region | {lead['region'] or 'Not provided'} |",

        f"| Industry | {lead['industry']} |",

        f"| Deal Value | USD {int(lead['deal_value_usd']):,} |",

        f"| Proposal Age | {proposal_age} |",

        f"| Mode | {strategy['mode']} |",

        f"| Commercial Priority | {strategy['priority']} |",

        f"| Score | {score_display} |",

        f"| Tier | {lead['tier'] or 'N/A'} |",

        f"| Engagement | {lead['engagement_signal'] or 'Not provided'} |",

        f"| Language | {profile['language']} |",

        f"| Default Channel | {profile['channel']} |",

        (
            "| Cadence | "
            + " / ".join(
                f"Day +{day}"
                for day in strategy[
                    "cadence_days"
                ]
            )
            + " |"
        ),

        f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M')} |",

        "",

        "## Internal Commercial Strategy",

        "",

        (
            "**Recommended Action:** "
            + (
                lead[
                    "recommended_action"
                ]
                or "Not provided"
            )
        ),

        "",

        (
            "**Commercial Objective:** "
            + strategy[
                "commercial_objective"
            ]
        ),

        "",

        "---",

        "",
    ]

    for key in [
        "day_1",
        "day_3",
        "day_7",
        "day_14",
    ]:

        msg = sequence.get(
            key,
            {},
        )

        lines.append(
            f"## {msg.get('label', key.upper())}"
        )

        lines.append(
            f"**Timing:** "
            f"{msg.get('timing', '')}"
        )

        lines.append(
            f"**Channel:** "
            f"{msg.get('channel', profile['channel'])}"
        )

        if msg.get(
            "subject"
        ):

            lines.append(
                f"**Subject:** "
                f"{msg['subject']}"
            )

        lines.append(
            ""
        )

        lines.append(
            msg.get(
                "message",
                "",
            )
        )

        lines.append(
            ""
        )

        lines.append(
            "---"
        )

        lines.append(
            ""
        )

    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "\n".join(
                lines
            )
        )

    return filepath


# ----------------------------------------------------------------------
# 11. CLI
# ----------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Adaptive multilingual outreach "
            "and commercial follow-up generator"
        )
    )

    parser.add_argument(
        "--input",
        default="pipeline.csv",
        help=(
            "Legacy outreach CSV or "
            "Lead Qualification export"
        ),
    )

    parser.add_argument(
        "--lead",
        default=None,
        help=(
            "Filter by company name"
        ),
    )

    parser.add_argument(
        "--output",
        default="sequences",
        help=(
            "Output folder"
        ),
    )

    args = parser.parse_args()

    os.makedirs(
        args.output,
        exist_ok=True,
    )

    df = pd.read_csv(
        args.input
    )

    leads = [

        normalize_lead(
            row
        )

        for _, row
        in df.iterrows()
    ]

    if args.lead:

        leads = [

            lead

            for lead in leads

            if args.lead.lower()
            in lead[
                "company"
            ].lower()
        ]

        if not leads:

            print(
                f"No lead found matching "
                f"'{args.lead}'"
            )

            return

    has_api = bool(
        os.environ.get(
            "ANTHROPIC_API_KEY"
        )
    )

    if not has_api:

        print(
            "\n[Info] ANTHROPIC_API_KEY not set."
        )

        print(
            "Local deterministic outreach "
            "generation will be used.\n"
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"ADAPTIVE OUTREACH INTELLIGENCE — "
        f"{len(leads)} lead(s)"
    )

    print(
        "=" * 70
        + "\n"
    )

    for lead in leads:

        profile = (
            COUNTRY_PROFILE.get(
                lead[
                    "country"
                ],
                DEFAULT_PROFILE,
            )
        )

        strategy = (
            build_outreach_strategy(
                lead,
                profile,
            )
        )

        print(
            f"→ {lead['company']}"
        )

        print(
            f"  Mode: "
            f"{strategy['mode']}"
        )

        print(
            f"  Priority: "
            f"{strategy['priority']}"
        )

        print(
            f"  Stage: "
            f"{strategy['stage']}"
        )

        print(
            f"  Language: "
            f"{profile['language']}"
        )

        print(
            f"  Channel: "
            f"{profile['channel']}"
        )

        print(
            "  Cadence: "
            + " / ".join(
                f"Day +{day}"
                for day in strategy[
                    "cadence_days"
                ]
            )
        )

        sequence = (
            generate_sequence(
                lead,
                profile,
            )
        )

        path = (
            save_markdown(
                lead,
                profile,
                sequence,
                args.output,
            )
        )

        print(
            f"  ✓ Saved → "
            f"{path}"
        )

        first_touch = (
            sequence.get(
                "day_1",
                {},
            )
        )

        print(
            "\n  First touch preview:"
        )

        if first_touch.get(
            "subject"
        ):

            print(
                "  Subject: "
                + first_touch[
                    "subject"
                ]
            )

        preview = (
            first_touch.get(
                "message",
                "",
            )[:300]
        )

        for line in preview.split(
            "\n"
        ):

            print(
                f"  {line}"
            )

        print()

    print(
        f"All sequences saved to: "
        f"./{args.output}/"
    )


if __name__ == "__main__":
    main()
