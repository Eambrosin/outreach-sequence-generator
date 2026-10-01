import pandas as pd

from field_planner import build_field_day_plan


def _pipeline():
    return pd.DataFrame(
        [
            {
                "company": "Clinic A",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Milano",
                "territory_city": "Milano",
                "contact_status": "Ready for Field Visit",
                "priority": "High",
                "visit_priority": "Visit Now",
                "visit_priority_score": 92,
                "product_fit_family": "CRISTAL Pro",
                "product_fit_score": 85,
                "planning_opportunity_value_eur": 30000,
                "account_opportunity_score": 90,
                "contact_readiness_score": 88,
                "score": 91,
                "field_visit_objective": "Validate current body-contouring need.",
                "field_opening_questions": "What technologies are installed?",
            },
            {
                "company": "Clinic B",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Lombardia",
                "territory_province": "Milano",
                "territory_city": "Milano",
                "contact_status": "Ready for Outreach",
                "priority": "High",
                "visit_priority": "Contact / Prepare First",
                "visit_priority_score": 65,
                "product_fit_family": "ORIGIN",
                "product_fit_score": 70,
                "planning_opportunity_value_eur": 25000,
                "account_opportunity_score": 86,
                "contact_readiness_score": 68,
                "score": 84,
            },
            {
                "company": "Clinic C",
                "territory_profile_id": "it_north_medical_aesthetics",
                "territory_region": "Veneto",
                "territory_province": "Verona",
                "territory_city": "Verona",
                "contact_status": "Ready for Field Visit",
                "priority": "High",
                "visit_priority": "High Priority Visit",
                "visit_priority_score": 82,
                "product_fit_family": "CONTOUR HIFU",
                "product_fit_score": 80,
                "planning_opportunity_value_eur": 40000,
                "account_opportunity_score": 88,
                "contact_readiness_score": 82,
                "score": 88,
            },
        ]
    )


def test_field_plan_prefers_visit_priority():
    plan = build_field_day_plan(_pipeline(), region="Lombardia", province="Milano", max_accounts=2)
    assert plan.iloc[0]["company"] == "Clinic A"
    assert plan.iloc[0]["visit_priority"] == "Visit Now"
    assert plan.iloc[0]["planning_opportunity_value_eur"] == 30000
    assert "product_fit_family" in plan.columns


def test_field_plan_filters_city():
    plan = build_field_day_plan(
        _pipeline(),
        region="Veneto",
        province="Verona",
        city="Verona",
        max_accounts=5,
    )
    assert plan["company"].tolist() == ["Clinic C"]


def test_field_plan_uses_explicit_visit_objective():
    plan = build_field_day_plan(_pipeline(), city="Milano", max_accounts=1)
    assert plan.iloc[0]["field_objective"] == "Validate current body-contouring need."
