import unittest

from commercial_deal import build_commercial_deal_sheet


class CommercialDealSheetTests(unittest.TestCase):
    def test_deal_sheet_preserves_mandate_and_trade_context(self):
        lead = {
            "company": "Example Buyer",
            "contact_name": "Ana Silva",
            "country": "Brazil",
            "industry": "Food Manufacturing",
            "mandate_name": "Italian machinery to Brazil",
            "mandate_corridor": "Italy → Brazil",
            "mandate_product": "Packaging machinery",
            "trade_feasibility_status": "In Review",
            "trade_ex_tarifario_status": "To Verify",
        }

        deal = build_commercial_deal_sheet(
            lead,
            deal_stage="Commercial Proposal",
            quantity="1 line",
            indicative_value=250000,
            currency="EUR",
            incoterm="FCA",
            next_step="Technical call",
        )

        self.assertEqual(deal["company_name"], "Example Buyer")
        self.assertEqual(deal["deal_product"], "Packaging machinery")
        self.assertEqual(deal["deal_indicative_value"], 250000)
        self.assertEqual(deal["mandate_name"], "Italian machinery to Brazil")
        self.assertEqual(deal["trade_feasibility_status"], "In Review")
        self.assertEqual(deal["deal_next_step"], "Technical call")


if __name__ == "__main__":
    unittest.main()
