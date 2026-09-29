from __future__ import annotations

import pandas as pd


STATUS_PRIORITY = {
    "Ready for Field Visit": 5,
    "Ready for Outreach": 4,
    "Verify Contact": 3,
    "Find Decision Maker": 2,
    "Research Contact": 1,
}

COMMERCIAL_PRIORITY = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def build_field_day_plan(
    dataframe: pd.DataFrame,
    *,
    region: str = "",
    province: str = "",
    max_accounts: int = 5,
) -> pd.DataFrame:
    """
    Build a province/city-clustered field-sales shortlist.

    This is deliberately not a route-optimization engine. It ranks accounts
    within a selected geographic cluster so a commercial user can plan visits
    without pretending to calculate drive time or optimal routing.
    """

    if dataframe.empty:
        return pd.DataFrame()

    df = dataframe.copy()

    if "territory_profile_id" not in df.columns:
        return pd.DataFrame()

    df = df[
        df["territory_profile_id"].fillna("").astype(str).str.strip() != ""
    ].copy()

    if region and "territory_region" in df.columns:
        df = df[df["territory_region"].astype(str) == region]

    if province and "territory_province" in df.columns:
        df = df[df["territory_province"].astype(str) == province]

    if df.empty:
        return pd.DataFrame()

    df["_status_rank"] = (
        df.get("contact_status", pd.Series([""] * len(df), index=df.index))
        .astype(str)
        .map(STATUS_PRIORITY)
        .fillna(0)
    )

    df["_priority_rank"] = (
        df.get("priority", pd.Series([""] * len(df), index=df.index))
        .astype(str)
        .map(COMMERCIAL_PRIORITY)
        .fillna(0)
    )

    for column in [
        "account_opportunity_score",
        "contact_readiness_score",
        "score",
    ]:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df = df.sort_values(
        [
            "_status_rank",
            "_priority_rank",
            "contact_readiness_score",
            "account_opportunity_score",
            "score",
        ],
        ascending=[False, False, False, False, False],
    ).head(max_accounts)

    plan = pd.DataFrame(
        {
            "visit_order": range(1, len(df) + 1),
            "company": df.get("company", ""),
            "contact_name": df.get("contact_name", ""),
            "territory_region": df.get("territory_region", ""),
            "territory_province": df.get("territory_province", ""),
            "territory_city": df.get("territory_city", ""),
            "public_address": df.get("public_address", ""),
            "public_phone": df.get("public_phone", ""),
            "public_email": df.get("public_email", ""),
            "account_website": df.get("account_website", ""),
            "enrichment_status": df.get("enrichment_status", ""),
            "contact_status": df.get("contact_status", ""),
            "priority": df.get("priority", ""),
            "account_opportunity_score": df.get("account_opportunity_score", 0),
            "contact_readiness_score": df.get("contact_readiness_score", 0),
            "linkedin_url": df.get("linkedin_url", ""),
            "field_objective": df.apply(_field_objective, axis=1),
        }
    )

    return plan.reset_index(drop=True)


def _field_objective(row: pd.Series) -> str:
    status = str(row.get("contact_status", "")).strip()
    territory_status = str(row.get("territory_status", "")).strip()

    if status == "Ready for Field Visit":
        return "Prepare a focused visit objective and confirm appointment / availability."
    if status == "Ready for Outreach":
        return "Secure a conversation before adding the account to a field-visit day."
    if territory_status == "Find Decision Maker":
        return "Identify and verify the decision maker before planning a visit."
    if territory_status == "Eligibility Validation":
        return "Validate professional/device eligibility before device-specific engagement."
    return "Complete desk research and establish a verified commercial next step."
