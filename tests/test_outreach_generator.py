from outreach_generator import (
    build_outreach_strategy,
    normalize_lead,
)


def test_lead_scorer_export_is_detected_as_commercial_intelligence():
    row = {
        "company_name": "Test Company",
        "country": "Italy",
        "region": "EU",
        "industry": "Renewable Energy",
        "company_size": 300,
        "estimated_deal_value_usd": 500000,
        "engagement_signal": "hot",
        "score": 88,
        "tier": "A",
        "recommended_action": "Immediate personalized outreach",
    }

    lead = normalize_lead(row)

    assert lead["company"] == "Test Company"
    assert lead["commercial_intelligence_mode"] is True
    assert lead["score"] == 88
    assert lead["tier"] == "A"


def test_tier_a_receives_high_priority():
    lead = normalize_lead(
        {
            "company_name": "High Priority Company",
            "country": "UAE",
            "industry": "Logistics & Trade",
            "estimated_deal_value_usd": 500000,
            "engagement_signal": "warm",
            "score": 82,
            "tier": "A",
        }
    )

    strategy = build_outreach_strategy(lead)

    assert strategy["priority"] == "High"
    assert strategy["intensity"] == "high-touch"


def test_high_priority_uses_shorter_cadence():
    lead = normalize_lead(
        {
            "company_name": "Priority Company",
            "country": "Brazil",
            "industry": "Agribusiness",
            "estimated_deal_value_usd": 800000,
            "engagement_signal": "hot",
            "tier": "A",
        }
    )

    strategy = build_outreach_strategy(lead)

    assert strategy["cadence_days"] == [0, 2, 5, 10]


def test_low_priority_cold_lead_uses_longer_cadence():
    lead = normalize_lead(
        {
            "company_name": "Low Priority Company",
            "country": "Italy",
            "industry": "Real Estate",
            "estimated_deal_value_usd": 50000,
            "engagement_signal": "cold",
            "tier": "C",
        }
    )

    strategy = build_outreach_strategy(lead)

    assert strategy["priority"] == "Low"
    assert strategy["cadence_days"] == [0, 7, 21, 35]


def test_legacy_pipeline_remains_supported():
    lead = normalize_lead(
        {
            "contact_name": "John Smith",
            "company": "Legacy Company",
            "country": "UK",
            "industry": "Logistics & Trade",
            "deal_type": "Commercial Proposal",
            "deal_value_usd": 200000,
            "proposal_sent_days_ago": 5,
            "your_name": "Eduardo Ambrosin",
        }
    )

    assert lead["company"] == "Legacy Company"
    assert lead["commercial_intelligence_mode"] is False
    assert lead["outreach_stage"] == "post_proposal"


def test_pipeline_without_proposal_is_prospecting():
    lead = normalize_lead(
        {
            "company_name": "Prospecting Company",
            "country": "Spain",
            "industry": "Fintech",
            "estimated_deal_value_usd": 150000,
            "score": 70,
            "tier": "B",
        }
    )

    assert lead["outreach_stage"] == "prospecting"


def test_aged_proposal_receives_high_priority():
    lead = normalize_lead(
        {
            "company": "Proposal Company",
            "country": "United Kingdom",
            "deal_value_usd": 100000,
            "proposal_sent_days_ago": 12,
        }
    )
    strategy = build_outreach_strategy(lead)
    assert strategy["priority"] == "High"
    assert "proposal status" in strategy["commercial_objective"].lower()


def test_unknown_country_uses_default_profile():
    lead = normalize_lead(
        {
            "company_name": "Unknown Market Company",
            "country": "Exampleland",
            "estimated_deal_value_usd": 100000,
            "tier": "B",
        }
    )
    strategy = build_outreach_strategy(lead)
    assert strategy["language"] == "English"
    assert strategy["primary_channel"] == "Email"


def test_uae_profile_switches_from_email_to_whatsapp():
    from outreach_generator import COUNTRY_PROFILE, channel_for_touch

    profile = COUNTRY_PROFILE["UAE"]
    assert channel_for_touch(profile, 1) == "Email"
    assert channel_for_touch(profile, 2) == "WhatsApp"


def test_local_sequence_does_not_expose_internal_score():
    from outreach_generator import COUNTRY_PROFILE, generate_local_sequence

    lead = normalize_lead(
        {
            "company_name": "Private Score Company",
            "country": "Italy",
            "estimated_deal_value_usd": 250000,
            "score": 91,
            "tier": "A",
            "engagement_signal": "hot",
            "score_rationale": "Internal scoring detail",
        }
    )
    profile = COUNTRY_PROFILE["Italy"]
    strategy = build_outreach_strategy(lead, profile)
    sequence = generate_local_sequence(lead, profile, strategy)

    combined = " ".join(
        item["message"]
        for item in sequence.values()
    ).lower()

    assert "91" not in combined
    assert "internal scoring detail" not in combined
    assert "tier a" not in combined
