import pandas as pd

from field_planner import build_field_day_plan
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


def test_medical_aesthetics_preserves_upstream_contact_intelligence():
    lead = normalize_lead(
        {
            "contact_name": "Dr. Giulia Rossi",
            "company_name": "Example Clinic",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "estimated_deal_value_usd": 75000,
            "engagement_signal": "warm",
            "score": 84,
            "tier": "A",
            "market_profile_id": "medical_aesthetics",
            "source_stage": "PRIORITIZE",
            "linkedin_url": "https://www.linkedin.com/in/example",
            "contact_headline": "Medical Director",
            "outreach_angle": "Clinical fit, training and patient-development support",
            "professional_setting": "Medical-setting signal observed",
        }
    )

    assert lead["market_profile_id"] == "medical_aesthetics"
    assert lead["linkedin_url"].startswith("https://www.linkedin.com/")
    assert lead["contact_headline"] == "Medical Director"
    assert lead["outreach_angle"]


def test_medical_aesthetics_strategy_adds_domain_validation():
    lead = normalize_lead(
        {
            "company_name": "Aesthetic Center",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "estimated_deal_value_usd": 50000,
            "engagement_signal": "cold",
            "professional_setting": "Professional/device eligibility to validate",
            "outreach_angle": "Treatment portfolio and staff training",
        }
    )

    strategy = build_outreach_strategy(lead)
    objective = strategy["commercial_objective"].lower()

    assert "treatment portfolio" in objective
    assert "eligibility" in objective
    assert "upstream research" in objective


def test_territory_metadata_and_contact_readiness_are_preserved():
    lead = normalize_lead(
        {
            "company_name": "Milano Aesthetic Clinic",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "market_profile_id": "medical_aesthetics",
            "territory_profile_id": "it_north_medical_aesthetics",
            "vendor_profile_id": "deleo_north_italy",
            "territory_region": "Lombardia",
            "territory_province": "Milano",
            "territory_city": "Milano",
            "territory_status": "Find Decision Maker",
            "account_opportunity_score": 89,
            "contact_readiness_score": 86,
            "contact_status": "Ready for Field Visit",
            "observed_technology_axes": "Silhouette / Body Contouring",
            "estimated_deal_value_usd": 90000,
            "tier": "A",
        }
    )

    assert lead["territory_profile_id"] == "it_north_medical_aesthetics"
    assert lead["vendor_profile_id"] == "deleo_north_italy"
    assert lead["territory_province"] == "Milano"
    assert lead["account_opportunity_score"] == 89
    assert lead["contact_readiness_score"] == 86
    assert lead["contact_status"] == "Ready for Field Visit"


def test_ready_contact_generates_field_visit_motion():
    lead = normalize_lead(
        {
            "company_name": "Verona Clinic",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "territory_profile_id": "it_north_medical_aesthetics",
            "territory_region": "Veneto",
            "territory_province": "Verona",
            "territory_city": "Verona",
            "contact_status": "Ready for Field Visit",
            "account_opportunity_score": 91,
            "estimated_deal_value_usd": 100000,
            "tier": "A",
        }
    )
    strategy = build_outreach_strategy(lead)
    assert strategy["field_motion"] == "Field visit candidate"


def test_south_tyrol_adds_language_verification_note():
    lead = normalize_lead(
        {
            "company_name": "Bozen Aesthetic Medizin",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "territory_profile_id": "it_north_medical_aesthetics",
            "territory_region": "Trentino-Alto Adige",
            "territory_province": "Bolzano / Bozen",
            "territory_city": "Bozen",
            "estimated_deal_value_usd": 80000,
            "tier": "B",
        }
    )
    strategy = build_outreach_strategy(lead)
    assert "German" in strategy["territory_language_note"]
    assert "Italian" in strategy["territory_language_note"]


def test_field_day_plan_prioritizes_ready_visit_accounts():
    dataframe = pd.DataFrame(
        [
            {
                "company": "Research Account",
                "contact_name": "",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Bergamo",
                "territory_city": "Bergamo",
                "territory_status": "Find Decision Maker",
                "contact_status": "",
                "priority": "High",
                "account_opportunity_score": 90,
                "contact_readiness_score": 0,
                "score": 85,
                "linkedin_url": "",
            },
            {
                "company": "Visit Ready Account",
                "contact_name": "Dr. Rossi",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Bergamo",
                "territory_city": "Bergamo",
                "territory_status": "Find Decision Maker",
                "contact_status": "Ready for Field Visit",
                "priority": "High",
                "account_opportunity_score": 88,
                "contact_readiness_score": 92,
                "score": 82,
                "linkedin_url": "https://www.linkedin.com/in/example",
            },
        ]
    )

    plan = build_field_day_plan(
        dataframe,
        region="Lombardia",
        province="Bergamo",
        max_accounts=5,
    )

    assert plan.iloc[0]["company"] == "Visit Ready Account"
    assert plan.iloc[0]["visit_order"] == 1


def test_field_day_plan_is_cluster_filterable():
    dataframe = pd.DataFrame(
        [
            {
                "company": "Milano Account",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Milano",
                "territory_city": "Milano",
                "priority": "High",
                "contact_status": "Ready for Outreach",
            },
            {
                "company": "Verona Account",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Veneto",
                "territory_province": "Verona",
                "territory_city": "Verona",
                "priority": "High",
                "contact_status": "Ready for Field Visit",
            },
        ]
    )

    plan = build_field_day_plan(
        dataframe,
        region="Veneto",
        province="Verona",
        max_accounts=5,
    )

    assert len(plan) == 1
    assert plan.iloc[0]["company"] == "Verona Account"
