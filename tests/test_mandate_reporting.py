import unittest

import pandas as pd

from mandate_reporting import build_mandate_report, report_to_markdown


class MandateReportingTests(unittest.TestCase):
    def test_report_counts_recorded_execution_only(self):
        pipeline = pd.DataFrame(
            [
                {
                    "company": "A",
                    "tier": "A",
                    "qualification_status": "Commercially Qualified",
                    "mandate_name": "EU to Brazil",
                },
                {
                    "company": "B",
                    "tier": "B",
                    "qualification_status": "Partially Qualified",
                    "mandate_name": "EU to Brazil",
                },
            ]
        )

        executions = [
            {
                "company_name": "A",
                "opportunity_stage": "Active Opportunity",
                "response_status": "Positive Response",
                "meeting_outcome": "Qualified technical discussion",
                "next_action": "Send quotation",
                "next_action_date": "2026-10-20",
                "mandate_name": "EU to Brazil",
            }
        ]

        deals = [
            {
                "company_name": "A",
                "deal_stage": "Quotation Submitted",
                "deal_indicative_value": 200000,
                "deal_currency": "EUR",
                "deal_next_step": "Follow up quotation",
                "mandate_name": "EU to Brazil",
            }
        ]

        report = build_mandate_report(
            pipeline,
            execution_updates=executions,
            deal_sheets=deals,
        )

        self.assertEqual(report["total_counterparties"], 2)
        self.assertEqual(report["qualified_counterparties"], 1)
        self.assertEqual(report["high_priority_counterparties"], 1)
        self.assertEqual(report["contacted"], 1)
        self.assertEqual(report["responses"], 1)
        self.assertEqual(report["meetings"], 1)
        self.assertEqual(report["active_opportunities"], 1)
        self.assertEqual(report["quotations"], 1)
        self.assertEqual(
            report["pipeline_value_by_currency"]["EUR"],
            200000,
        )

        markdown = report_to_markdown(report)
        self.assertIn("Commercial Mandate Report", markdown)
        self.assertIn("Send quotation", markdown)


if __name__ == "__main__":
    unittest.main()
