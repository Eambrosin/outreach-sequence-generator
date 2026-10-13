import unittest

from bd_execution import build_execution_update


class BusinessDevelopmentExecutionTests(unittest.TestCase):
    def test_execution_update_preserves_mandate_and_next_action(self):
        lead = {
            "company": "Example Buyer",
            "contact_name": "Ana Silva",
            "country": "Brazil",
            "industry": "Food Manufacturing",
            "score": 82,
            "tier": "A",
            "mandate_name": "Italy to Brazil machinery",
            "mandate_corridor": "Italy → Brazil",
            "mandate_product": "Packaging machinery",
            "trade_feasibility_status": "In Review",
        }

        update = build_execution_update(
            lead,
            opportunity_stage="Meeting Completed",
            response_status="Positive Response",
            meeting_outcome="Technical follow-up requested",
            next_action="Send technical documentation",
            next_action_date="2026-10-20",
        )

        self.assertEqual(update["source_stage"], "ENGAGE_EXECUTION")
        self.assertEqual(update["company_name"], "Example Buyer")
        self.assertEqual(update["mandate_name"], "Italy to Brazil machinery")
        self.assertEqual(update["trade_feasibility_status"], "In Review")
        self.assertEqual(update["next_action"], "Send technical documentation")


if __name__ == "__main__":
    unittest.main()
