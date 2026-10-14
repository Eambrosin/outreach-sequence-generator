import unittest

from workspace_snapshot import (
    WORKSPACE_SNAPSHOT_SCHEMA_VERSION,
    build_workspace_snapshot,
    snapshot_filename,
    snapshot_from_json,
    snapshot_to_json,
)


class WorkspaceSnapshotTests(unittest.TestCase):
    def test_snapshot_round_trip(self):
        snapshot = build_workspace_snapshot(
            mandate={
                "mandate_name": "Italy to Brazil machinery",
                "mandate_client": "Example Manufacturer",
                "mandate_product": "Packaging machinery",
            },
            pipeline_records=[
                {
                    "company": "Buyer A",
                    "country": "Brazil",
                }
            ],
            execution_updates=[
                {
                    "company_name": "Buyer A",
                    "opportunity_stage": "Active Opportunity",
                }
            ],
            deal_sheets=[
                {
                    "company_name": "Buyer A",
                    "deal_stage": "Quotation Submitted",
                    "deal_indicative_value": 120000,
                    "deal_currency": "EUR",
                }
            ],
            source_name="pipeline.csv",
        )

        encoded = snapshot_to_json(snapshot)
        restored = snapshot_from_json(encoded)

        self.assertEqual(
            restored["workspace_snapshot_schema_version"],
            WORKSPACE_SNAPSHOT_SCHEMA_VERSION,
        )
        self.assertEqual(
            restored["mandate"]["mandate_client"],
            "Example Manufacturer",
        )
        self.assertEqual(len(restored["pipeline"]), 1)
        self.assertEqual(len(restored["execution_updates"]), 1)
        self.assertEqual(len(restored["deal_sheets"]), 1)

    def test_snapshot_filename_uses_mandate_name(self):
        snapshot = build_workspace_snapshot(
            mandate={"mandate_name": "Italy → Brazil Machinery"},
            pipeline_records=[],
        )
        self.assertEqual(
            snapshot_filename(snapshot),
            "italy_brazil_machinery_workspace_snapshot.json",
        )

    def test_rejects_unknown_schema_version(self):
        with self.assertRaises(ValueError):
            snapshot_from_json(
                '{"workspace_snapshot_schema_version":"9.0"}'
            )


if __name__ == "__main__":
    unittest.main()
