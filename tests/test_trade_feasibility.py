import unittest

import pandas as pd

from trade_feasibility import (
    TradeFeasibility,
    TRADE_FEASIBILITY_FIELDS,
    apply_trade_feasibility_fields,
    feasibility_from_mapping,
)


class TradeFeasibilityTests(unittest.TestCase):
    def test_trade_feasibility_round_trip(self):
        context = TradeFeasibility(
            trade_feasibility_status="In Review",
            trade_tariff_scenario_status="To Verify",
            trade_ex_tarifario_status="Unknown",
            trade_after_sales_status="To Verify",
        )
        payload = context.to_dict()
        self.assertEqual(payload["trade_feasibility_schema_version"], "1.0")
        self.assertEqual(payload["trade_feasibility_status"], "In Review")

    def test_apply_trade_fields_preserves_project_context(self):
        frame = pd.DataFrame([{"company_name": "A"}])
        result = apply_trade_feasibility_fields(
            frame,
            {
                "trade_feasibility_status": "To Verify",
                "trade_rules_of_origin_status": "In Review",
            },
        )
        self.assertTrue(set(TRADE_FEASIBILITY_FIELDS).issubset(result.columns))
        self.assertEqual(result.iloc[0]["trade_rules_of_origin_status"], "In Review")

    def test_unknown_fields_remain_explicit(self):
        payload = feasibility_from_mapping({})
        self.assertEqual(payload["trade_feasibility_status"], "")
        self.assertEqual(payload["trade_feasibility_schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
