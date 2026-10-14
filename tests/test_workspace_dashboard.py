import unittest
from datetime import date

from workspace_dashboard import (
    action_priority,
    action_status,
    build_next_action_queue,
    workspace_counts,
)


class WorkspaceDashboardTests(unittest.TestCase):
    def test_action_status(self):
        today = date(2026, 10, 14)
        self.assertEqual(
            action_status("2026-10-13", today=today),
            "Overdue",
        )
        self.assertEqual(
            action_status("2026-10-14", today=today),
            "Due Today",
        )
        self.assertEqual(
            action_status("2026-10-15", today=today),
            "Upcoming",
        )
        self.assertEqual(
            action_status("", today=today),
            "Unscheduled",
        )

    def test_high_priority_for_active_opportunity(self):
        self.assertEqual(
            action_priority(
                {
                    "opportunity_stage": "Active Opportunity",
                    "upstream_tier": "B",
                }
            ),
            "High",
        )

    def test_queue_orders_overdue_before_upcoming(self):
        rows = build_next_action_queue(
            [
                {
                    "company_name": "Later",
                    "opportunity_stage": "Qualification",
                    "next_action": "Follow up",
                    "next_action_date": "2026-10-20",
                    "upstream_tier": "B",
                },
                {
                    "company_name": "Urgent",
                    "opportunity_stage": "Active Opportunity",
                    "next_action": "Send quotation",
                    "next_action_date": "2026-10-13",
                    "upstream_tier": "A",
                },
            ],
            today=date(2026, 10, 14),
        )
        self.assertEqual(rows[0]["Company"], "Urgent")
        self.assertEqual(rows[0]["Status"], "Overdue")
        self.assertEqual(rows[0]["Priority"], "High")

    def test_workspace_counts(self):
        counts = workspace_counts(
            {
                "pipeline": [{}, {}],
                "execution_updates": [{}],
                "deal_sheets": [{}],
                "field_visit_feedback": [{}, {}, {}],
            }
        )
        self.assertEqual(counts["pipeline"], 2)
        self.assertEqual(counts["execution_updates"], 1)
        self.assertEqual(counts["deal_sheets"], 1)
        self.assertEqual(counts["field_visit_feedback"], 3)


if __name__ == "__main__":
    unittest.main()
