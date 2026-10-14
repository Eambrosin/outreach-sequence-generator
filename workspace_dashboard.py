from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "<na>", "null"} else text


def _date_value(value: Any) -> date | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def action_status(value: Any, *, today: date | None = None) -> str:
    due = _date_value(value)
    if due is None:
        return "Unscheduled"
    today = today or date.today()
    if due < today:
        return "Overdue"
    if due == today:
        return "Due Today"
    return "Upcoming"


def action_priority(item: Mapping[str, Any]) -> str:
    stage = _clean(item.get("opportunity_stage"))
    tier = _clean(item.get("upstream_tier") or item.get("tier")).upper()

    if stage in {"Negotiation", "Quotation / Proposal", "Active Opportunity"}:
        return "High"
    if tier == "A":
        return "High"
    if stage in {"Meeting Scheduled", "Meeting Completed", "Qualification"}:
        return "Medium"
    if tier == "B":
        return "Medium"
    return "Normal"


def build_next_action_queue(
    execution_updates: Iterable[Mapping[str, Any]] | None,
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    today = today or date.today()
    rows = []

    for source in execution_updates or []:
        item = dict(source)
        next_action = _clean(item.get("next_action"))
        if not next_action:
            continue

        due = _clean(item.get("next_action_date"))
        rows.append(
            {
                "Company": _clean(
                    item.get("company_name")
                    or item.get("company")
                ) or "Unnamed account",
                "Stage": _clean(item.get("opportunity_stage")) or "To qualify",
                "Next Action": next_action,
                "Due": due,
                "Priority": action_priority(item),
                "Status": action_status(due, today=today),
            }
        )

    status_order = {
        "Overdue": 0,
        "Due Today": 1,
        "Upcoming": 2,
        "Unscheduled": 3,
    }
    priority_order = {
        "High": 0,
        "Medium": 1,
        "Normal": 2,
    }

    def sort_key(row: Mapping[str, Any]):
        due = _date_value(row.get("Due")) or date.max
        return (
            status_order.get(_clean(row.get("Status")), 9),
            due,
            priority_order.get(_clean(row.get("Priority")), 9),
            _clean(row.get("Company")).lower(),
        )

    rows.sort(key=sort_key)
    return rows


def workspace_counts(snapshot: Mapping[str, Any] | None) -> dict[str, int]:
    payload = dict(snapshot or {})
    return {
        "pipeline": len(payload.get("pipeline", []) or []),
        "execution_updates": len(payload.get("execution_updates", []) or []),
        "deal_sheets": len(payload.get("deal_sheets", []) or []),
        "field_visit_feedback": len(payload.get("field_visit_feedback", []) or []),
    }
