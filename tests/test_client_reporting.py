import unittest

from client_reporting import build_funnel_rows, client_report_to_markdown


class ClientReportingTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "mandate_summary": "Italy to Brazil · Packaging machinery",
            "mandate_context": {
                "mandate_client": "Example Manufacturer",
                "mandate_corridor": "Italy → Brazil",
                "mandate_target_market": "Brazil",
                "mandate_product": "Packaging machinery",
                "mandate_commercial_objective": "Develop qualified industrial buyers",
            },
            "total_counterparties": 20,
            "qualified_counterparties": 8,
            "contacted": 6,
            "responses": 4,
            "meetings": 3,
            "active_opportunities": 2,
            "quotations": 1,
            "won": 0,
            "pipeline_value_by_currency": {"EUR": 250000},
            "top_deals": [
                {
                    "company_name": "Buyer A",
                    "deal_stage": "Quotation Submitted",
                    "deal_indicative_value": 250000,
                    "deal_currency": "EUR",
                    "deal_next_step": "Technical follow-up",
                }
            ],
            "pending_actions": [
                {
                    "company_name": "Buyer A",
                    "next_action": "Technical follow-up",
                    "next_action_date": "2026-10-22",
                }
            ],
        }

    def test_funnel_uses_current_pipeline_as_denominator(self):
        rows = build_funnel_rows(self.report)
        self.assertEqual(rows[0]["Count"], 20)
        self.assertEqual(rows[1]["Share of current pipeline"], 40.0)
        self.assertEqual(rows[5]["Count"], 2)

    def test_client_report_contains_mandate_and_next_action(self):
        markdown = client_report_to_markdown(
            self.report,
            reporting_period="October 2026",
        )
        self.assertIn("Ambrosin Legal Trade", markdown)
        self.assertIn("Example Manufacturer", markdown)
        self.assertIn("October 2026", markdown)
        self.assertIn("Technical follow-up", markdown)


if __name__ == "__main__":
    unittest.main()
