import os
from unittest.mock import patch

import pandas as pd

from field_planner import build_field_day_plan
from outreach_generator import (
    build_outreach_strategy,
    generate_local_sequence,
    generate_sequence,
    normalize_lead,
    select_available_channel,
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


def test_nullable_enrichment_fields_do_not_become_literal_na_strings():
    lead = normalize_lead(
        {
            "company_name": "Example Clinic",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "account_website": pd.NA,
            "public_phone": pd.NA,
            "public_email": pd.NA,
            "public_address": pd.NA,
            "enrichment_status": pd.NA,
            "account_data_completeness": pd.NA,
        }
    )

    assert lead["account_website"] == ""
    assert lead["public_phone"] == ""
    assert lead["public_email"] == ""
    assert lead["public_address"] == ""
    assert lead["enrichment_status"] == ""
    assert lead["account_data_completeness"] == 0


def test_field_day_plan_preserves_enriched_visit_details():
    dataframe = pd.DataFrame(
        [
            {
                "company": "Visit Ready Clinic",
                "contact_name": "Dr. Rossi",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Milano",
                "territory_city": "Milano",
                "public_address": "Via Roma 10, Milano",
                "public_phone": "+39 02 1234 5678",
                "public_email": "info@exampleclinic.it",
                "account_website": "https://exampleclinic.it",
                "enrichment_status": "Enriched",
                "contact_status": "Ready for Field Visit",
                "priority": "High",
                "account_opportunity_score": 90,
                "contact_readiness_score": 92,
                "score": 88,
                "linkedin_url": "https://www.linkedin.com/in/example",
            }
        ]
    )

    plan = build_field_day_plan(
        dataframe,
        region="Lombardia",
        province="Milano",
        max_accounts=5,
    )

    row = plan.iloc[0]
    assert row["public_address"] == "Via Roma 10, Milano"
    assert row["public_phone"] == "+39 02 1234 5678"
    assert row["account_website"] == "https://exampleclinic.it"
    assert row["enrichment_status"] == "Enriched"


def test_evidence_aware_handoff_v2_is_preserved():
    lead = normalize_lead(
        {
            "schema_version": "2.0",
            "source_stage": "IDENTIFY_CONTACT_VALIDATED",
            "contact_name": "Alessandra Cecchini",
            "company": "Alessandra Cecchini",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "score": 76.8,
            "account_opportunity_score": 76.8,
            "qualification_readiness_score": 85,
            "qualification_readiness_status": "Ready for Qualification",
            "sales_motion": "Ready for Qualification Outreach",
            "buyer_access_status": "Practitioner candidate + public contact path observed",
            "commercial_hypothesis": "Public evidence supports commercial qualification.",
            "commercial_angle": "Qualification-first conversation.",
            "next_best_action": "Verify purchasing authority and current portfolio.",
            "qualification_questions": "Do you evaluate new technologies?",
            "sales_evidence_gaps": "decision authority / purchasing role | timing / active buying context",
            "public_contact_form": True,
            "linkedin_url": "https://it.linkedin.com/in/alessandra-cecchini",
            "professional_role_signal": "chirurgo estetico",
            "location_match_evidence": "milano, lombardia",
        }
    )

    assert lead["schema_version"] == "2.0"
    assert lead["sales_motion"] == "Ready for Qualification Outreach"
    assert lead["qualification_readiness_score"] == 85
    assert lead["public_contact_form"] is True
    assert lead["professional_role_signal"] == "chirurgo estetico"
    assert lead["commercial_intelligence_mode"] is True


def test_verified_available_channel_prefers_linkedin_over_unverified_whatsapp():
    lead = normalize_lead(
        {
            "company": "Alessandra Cecchini",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "linkedin_url": "https://it.linkedin.com/in/alessandra-cecchini",
            "public_contact_form": True,
            "public_phone": "",
            "public_email": "",
        }
    )

    channel = select_available_channel(
        lead,
        {"channel": "WhatsApp", "language": "Italian", "tone": "professional"},
    )

    assert channel == "LinkedIn"


def test_contact_form_is_used_when_no_direct_or_linkedin_channel_exists():
    lead = normalize_lead(
        {
            "company": "Example Practice",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "public_contact_form": True,
        }
    )

    channel = select_available_channel(
        lead,
        {"channel": "WhatsApp", "language": "Italian", "tone": "professional"},
    )

    assert channel == "Website Contact Form"


def test_ready_qualification_motion_uses_measured_linkedin_cadence():
    lead = normalize_lead(
        {
            "contact_name": "Alessandra Cecchini",
            "company": "Alessandra Cecchini",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "score": 76.8,
            "engagement_signal": "cold",
            "engagement_status": "unverified",
            "sales_motion": "Ready for Qualification Outreach",
            "sales_evidence_gaps": (
                "decision authority / purchasing role | "
                "current treatment / technology portfolio | "
                "timing / active buying context"
            ),
            "next_best_action": (
                "Use the observed public contact path to open a qualification-first conversation."
            ),
            "linkedin_url": "https://it.linkedin.com/in/alessandra-cecchini",
            "public_contact_form": True,
        }
    )

    strategy = build_outreach_strategy(lead)

    assert strategy["primary_channel"] == "LinkedIn"
    assert strategy["intensity"] == "qualification-first"
    assert strategy["cadence_days"] == [0, 3, 8, 16]
    assert "qualification-first" in strategy["commercial_objective"].lower()
    assert "active buying context" in strategy["commercial_objective"].lower()


def test_local_italian_medical_aesthetics_sequence_is_qualification_first():
    lead = normalize_lead(
        {
            "contact_name": "Alessandra Cecchini",
            "company": "Alessandra Cecchini",
            "country": "Italy",
            "industry": "Medical Aesthetics",
            "score": 76.8,
            "sales_motion": "Ready for Qualification Outreach",
            "linkedin_url": "https://it.linkedin.com/in/alessandra-cecchini",
            "territory_city": "Milano",
            "public_contact_form": True,
        }
    )

    profile = {
        "language": "Italian",
        "channel": "WhatsApp",
        "tone": "warm, polished and professional",
    }
    strategy = build_outreach_strategy(lead, profile)
    sequence = generate_local_sequence(lead, profile, strategy)

    assert sequence["day_1"]["channel"] == "LinkedIn"
    assert sequence["day_1"]["subject"] == ""
    assert "valutate nuove tecnologie" in sequence["day_1"]["message"].lower()
    assert "opportunità relative a alessandra cecchini" not in sequence["day_1"]["message"].lower()
    assert "valuta direttamente" in sequence["day_7"]["message"].lower()



def test_generate_sequence_falls_back_end_to_end_for_alessandra_handoff_v2():
    row = {
        "schema_version": "2.0",
        "source_stage": "IDENTIFY_CONTACT_VALIDATED",
        "contact_name": "Alessandra Cecchini",
        "company": "Alessandra Cecchini",
        "country": "Italy",
        "industry": "Medical Aesthetics",
        "deal_type": "Prospecting",
        "deal_value_usd": 0,
        "deal_value_status": "unknown",
        "engagement_signal": "cold",
        "engagement_status": "unverified",
        "score": 76.8,
        "account_opportunity_score": 76.8,
        "qualification_readiness_score": 90,
        "qualification_readiness_status": "Ready for Qualification",
        "sales_motion": "Ready for Qualification Outreach",
        "buyer_access_status": "Practitioner candidate + public contact path observed",
        "commercial_hypothesis": "Alessandra Cecchini appears worth commercial qualification.",
        "commercial_angle": "Lead with the market value proposition and validate fit.",
        "next_best_action": "Use the observed public contact path to open a qualification-first conversation.",
        "qualification_questions": "Do you personally evaluate and approve new technologies/equipment for the practice?",
        "sales_evidence_gaps": "decision authority / purchasing role | practice scale / operating footprint | current treatment / technology portfolio | timing / active buying context",
        "commercial_risk_flags": "decision-maker authority is not verified | active buying context has not been established",
        "linkedin_url": "https://it.linkedin.com/in/alessandra-cecchini",
        "contact_headline": "Chirurgo estetico - Loconlus ONLUS",
        "professional_role_signal": "chirurgo estetico",
        "location_match_evidence": "milano, lombardia",
        "public_contact_form": True,
        "territory_region": "Lombardia",
        "territory_province": "Milano",
        "territory_city": "Milano",
        "territory_status": "Strong Territory Prospect",
        "contact_readiness_score": 93.2,
        "contact_status": "Ready for Outreach",
    }

    profile = {
        "language": "Italian",
        "channel": "WhatsApp",
        "tone": "warm, polished and professional",
    }

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        sequence = generate_sequence(row, profile)

    assert set(sequence.keys()) == {
        "day_1",
        "day_3",
        "day_7",
        "day_14",
    }
    assert sequence["day_1"]["channel"] == "LinkedIn"
    assert sequence["day_1"]["subject"] == ""
    assert "Buongiorno Alessandra Cecchini" in sequence["day_1"]["message"]
    assert "valutate nuove tecnologie" in sequence["day_1"]["message"].lower()
    assert sequence["day_3"]["timing"] == "Day +3"
    assert sequence["day_7"]["timing"] == "Day +8"
    assert sequence["day_14"]["timing"] == "Day +16"
