import unittest

from mandate_workspace import APP_URLS, stage_url, workspace_plan


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

    def test_prioritize_buyer_mandate_progresses_to_engage(self):
        plan = workspace_plan(
            "PRIORITIZE",
            {"mandate_counterparty_focus": "Buyers"},
        )
        self.assertEqual(plan["next_stage"], "ENGAGE")
        self.assertIn("qualified buyers", plan["next_action"])

    def test_prioritize_partner_mandate_progresses_to_partner(self):
        plan = workspace_plan(
            "PRIORITIZE",
            {"mandate_counterparty_focus": "Partners"},
        )
        self.assertEqual(plan["next_stage"], "PARTNER")
        self.assertIn("partner candidates", plan["next_action"])

    def test_prioritize_mixed_mandate_splits_buyer_and_partner_paths(self):
        plan = workspace_plan(
            "PRIORITIZE",
            {"mandate_counterparty_focus": "Buyers + Partners"},
        )
        self.assertEqual(plan["next_stage"], "ENGAGE / PARTNER")
        self.assertIn("qualified buyers", plan["next_action"])
        self.assertIn("route-to-market partner candidates", plan["next_action"])

    def test_partner_progresses_to_engage(self):
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

    def test_stage_url_propagates_mandate_id(self):
        url = stage_url(
            "ENGAGE",
            {"mandate_id": "mandate_demo_123"},
        )
        self.assertIn(
            "mandate_id=mandate_demo_123",
            url,
        )

    def test_stage_url_without_mandate_id_keeps_base_url(self):
        self.assertEqual(
            stage_url("PARTNER", {}),
            APP_URLS["PARTNER"],
        )


if __name__ == "__main__":
    unittest.main()
