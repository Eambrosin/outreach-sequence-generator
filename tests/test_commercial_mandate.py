import unittest

import pandas as pd

from commercial_mandate import (
    CommercialMandate,
    MANDATE_FIELDS,
    apply_mandate_fields,
    has_mandate_context,
    mandate_filename,
    mandate_from_json,
    mandate_from_mapping,
    mandate_to_json,
)


class CommercialMandateTests(unittest.TestCase):
    def test_mandate_round_trip_preserves_context(self):
        mandate = CommercialMandate(
            mandate_name="Italy to Brazil industrial expansion",
            mandate_client="Example Manufacturer",
            mandate_corridor="Italy → Brazil",
            mandate_counterparty_focus="Buyers + Partners",
            mandate_origin_market="Italy",
            mandate_target_market="Brazil",
            mandate_product="Packaging machinery",
            mandate_commercial_objective="Develop qualified industrial buyers",
            mandate_target_partner_types="Distributor, Technical Service Partner",
        )
        payload = mandate.to_dict()
        self.assertEqual(payload["mandate_schema_version"], "1.0")
        self.assertEqual(payload["mandate_target_market"], "Brazil")
        self.assertEqual(payload["mandate_counterparty_focus"], "Buyers + Partners")
        self.assertTrue(has_mandate_context(payload))

    def test_portable_json_round_trip(self):
        mandate = CommercialMandate(
            mandate_name="Machinery Brazil",
            mandate_client="Example Manufacturer",
            mandate_corridor="Europe → Brazil / Mercosur",
            mandate_product="Packaging machinery",
        )
        encoded = mandate_to_json(mandate.to_dict())
        restored = mandate_from_json(encoded)
        self.assertEqual(restored["mandate_name"], "Machinery Brazil")
        self.assertEqual(restored["mandate_client"], "Example Manufacturer")
        self.assertEqual(restored["mandate_product"], "Packaging machinery")
        self.assertEqual(
            mandate_filename(restored),
            "machinery_brazil_mandate.json",
        )

    def test_apply_mandate_fields_keeps_same_context_for_every_row(self):
        frame = pd.DataFrame(
            [{"company_name": "A"}, {"company_name": "B"}]
        )
        result = apply_mandate_fields(
            frame,
            {
                "mandate_name": "EU to Brazil",
                "mandate_corridor": "Europe → Brazil / Mercosur",
                "mandate_product": "Industrial equipment",
            },
        )
        self.assertEqual(len(result), 2)
        self.assertTrue(set(MANDATE_FIELDS).issubset(result.columns))
        self.assertTrue((result["mandate_name"] == "EU to Brazil").all())

    def test_unknown_mandate_fields_remain_blank(self):
        payload = mandate_from_mapping({})
        self.assertEqual(payload["mandate_client"], "")
        self.assertEqual(payload["mandate_schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
