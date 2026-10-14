import unittest

from workspace_cloud import build_workspace_record, workspace_label


class WorkspaceCloudTests(unittest.TestCase):
    def test_workspace_record_uses_mandate_id(self):
        record = build_workspace_record(
            {
                "mandate": {
                    "mandate_id": "mandate_demo",
                    "mandate_name": "Italy to Brazil",
                },
                "pipeline": [],
            }
        )
        self.assertEqual(record["mandate_id"], "mandate_demo")
        self.assertEqual(record["workspace_id"], "workspace_mandate_demo")
        self.assertEqual(record["workspace_name"], "Italy to Brazil")

    def test_workspace_label_uses_name(self):
        label = workspace_label(
            {
                "workspace_name": "Brazil market entry",
                "updated_at": "2026-10-14T16:00:00+00:00",
            }
        )
        self.assertIn("Brazil market entry", label)


if __name__ == "__main__":
    unittest.main()
