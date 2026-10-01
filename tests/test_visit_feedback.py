from visit_feedback import build_visit_feedback


def test_demo_request_becomes_verified_hot_signal():
    result = build_visit_feedback(
        {"company": "Clinic A", "country": "Italy", "region": "Lombardia", "industry": "Medical Aesthetics"},
        outcome="Demo requested",
        estimated_value_eur=30000,
        current_technologies="HIFU competitor",
    )
    assert result["engagement_signal"] == "hot"
    assert result["engagement_status"] == "verified"
    assert result["deal_value_status"] == "verified"
    assert result["estimated_deal_value_eur"] == 30000
    assert result["source_stage"] == "FIELD_VISIT_FEEDBACK"


def test_no_value_remains_unknown():
    result = build_visit_feedback(
        {"company_name": "Clinic B", "country": "Italy", "territory_region": "Veneto"},
        outcome="Discovery completed",
    )
    assert result["company_name"] == "Clinic B"
    assert result["engagement_signal"] == "warm"
    assert result["deal_value_status"] == "unknown"
