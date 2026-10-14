import unittest

from mandate_workspace import APP_URLS, workspace_plan


class MandateWorkspaceTests(unittest.TestCase):
    def test_identify_buyer_mandate_progresses_to_prioritize(self):
        plan = workspace_plan(
            "IDENTIFY",
            {
                "mandate_name": "Italy to Brazil",
                "mandate_counterparty_focus": "Buyers",
                "mandate_product": "Packaging machinery",
            },
        )
        self.assertEqual(plan["next_stage"], "PRIORITIZE")
        self.assertTrue(plan["mandate_loaded"])

    def test_identify_partner_mandate_progresses_to_partner(self):
        plan = workspace_plan(
            "IDENTIFY",
            {
                "mandate_name": "Italy to Brazil",
                "mandate_counterparty_focus": "Partners",
            },
        )
        self.assertEqual(plan["next_stage"], "PARTNER")

    def test_partner_and_prioritize_progress_to_engage(self):
        self.assertEqual(
            workspace_plan("PRIORITIZE", {})["next_stage"],
            "ENGAGE",
        )
        self.assertEqual(
            workspace_plan("PARTNER", {})["next_stage"],
            "ENGAGE",
        )

    def test_engage_progresses_to_reporting(self):
        plan = workspace_plan("ENGAGE", {})
        self.assertEqual(plan["next_stage"], "REPORT")

    def test_all_module_urls_are_present(self):
        self.assertEqual(
            set(APP_URLS),
            {"IDENTIFY", "PRIORITIZE", "PARTNER", "ENGAGE"},
        )


if __name__ == "__main__":
    unittest.main()
