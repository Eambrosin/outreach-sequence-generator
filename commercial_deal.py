from __future__ import annotations

from typing import Any, Mapping

from commercial_mandate import mandate_from_mapping
from trade_feasibility import feasibility_from_mapping


DEAL_STAGES = [
    "Opportunity Identified",
    "Needs / Scope Validation",
    "Technical Validation",
    "Commercial Proposal",
    "Quotation Submitted",
    "Negotiation",
    "Contract / PO Review",
    "Won",
    "Lost",
    "On Hold",
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except Exception:
        pass
    return str(value).strip()


def _number(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def build_commercial_deal_sheet(
    lead: Mapping[str, Any],
    *,
    deal_stage: str,
    product: str = "",
    product_specification: str = "",
    quantity: str = "",
    indicative_value: float = 0.0,
    currency: str = "EUR",
    quotation_status: str = "",
    incoterm: str = "",
    payment_terms: str = "",
    moq: str = "",
    delivery_terms: str = "",
    warranty_terms: str = "",
    after_sales_model: str = "",
    exclusivity_terms: str = "",
    territory_terms: str = "",
    commission_terms: str = "",
    technical_validation: str = "",
    regulatory_validation: str = "",
    documents_exchanged: str = "",
    decision_makers: str = "",
    commercial_risks: str = "",
    next_step: str = "",
    next_step_date: str = "",
    deal_notes: str = "",
) -> dict[str, Any]:
    sheet = {
        "schema_version": "1.0",
        "source_stage": "ENGAGE_DEAL",
        "company_name": _clean(
            lead.get("company_name", lead.get("company", ""))
        ),
        "contact_name": _clean(lead.get("contact_name", "")),
        "country": _clean(lead.get("country", "")),
        "industry": _clean(lead.get("industry", "")),
        "deal_stage": _clean(deal_stage),
        "deal_product": _clean(
            product
            or lead.get("mandate_product", "")
        ),
        "deal_product_specification": _clean(product_specification),
        "deal_quantity": _clean(quantity),
        "deal_indicative_value": _number(indicative_value),
        "deal_currency": _clean(currency) or "EUR",
        "quotation_status": _clean(quotation_status),
        "incoterm": _clean(incoterm),
        "payment_terms": _clean(payment_terms),
        "moq": _clean(moq),
        "delivery_terms": _clean(delivery_terms),
        "warranty_terms": _clean(warranty_terms),
        "after_sales_model": _clean(after_sales_model),
        "exclusivity_terms": _clean(exclusivity_terms),
        "territory_terms": _clean(territory_terms),
        "commission_terms": _clean(commission_terms),
        "technical_validation": _clean(technical_validation),
        "regulatory_validation": _clean(regulatory_validation),
        "documents_exchanged": _clean(documents_exchanged),
        "decision_makers": _clean(decision_makers),
        "commercial_risks": _clean(commercial_risks),
        "deal_next_step": _clean(next_step),
        "deal_next_step_date": _clean(next_step_date),
        "deal_notes": _clean(deal_notes),
        "upstream_score": lead.get("score", ""),
        "upstream_tier": _clean(lead.get("tier", "")),
    }
    sheet.update(mandate_from_mapping(lead))
    sheet.update(feasibility_from_mapping(lead))
    return sheet
