import unittest
from tools.scraper_tool import is_valid_result

class TestScraperFilters(unittest.TestCase):
    def test_missing_title(self):
        valid, reason = is_valid_result("iphone 17", "", 900, "Amazon", "USD")
        self.assertFalse(valid)
        self.assertIn("Missing title", reason)

    def test_missing_query_intent(self):
        valid, reason = is_valid_result("iphone 17", "Generic Smartphone Black", 900, "Amazon", "USD")
        self.assertFalse(valid)
        self.assertIn("missing query intent", reason)

    def test_irrelevant_accessory(self):
        valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 Silicone Case", 50, "Amazon", "USD")
        self.assertFalse(valid)
        self.assertIn("exclusion keyword", reason)

    def test_valid_flagship_usd(self):
        valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 899, "Amazon", "USD")
        self.assertTrue(valid, f"Failed: {reason}")

    def test_valid_flagship_inr(self):
        # Now explicitly pass INR
        valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 89900, "Flipkart", "INR")
        self.assertTrue(valid, f"Failed: {reason}")

    def test_outlier_low_inr(self):
        valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 1500, "Flipkart", "INR")
        self.assertFalse(valid)
        self.assertIn("too low", reason)

    def test_accessory_query(self):
        valid, reason = is_valid_result("iphone 17 case", "Apple iPhone 17 Silicone Case", 49, "Amazon", "USD")
        self.assertTrue(valid, f"Failed: {reason}")

    def test_valid_mid_range_inr(self):
        # Passes INR explicitly instead of heuristic
        valid, reason = is_valid_result("redmi 13 5g", "Redmi 13 5G (6GB RAM)", 13999, "Amazon", "INR")
        self.assertTrue(valid, f"Failed: {reason}")

    def test_regression_amazon_inr_extraction(self):
        # Bug: When scraping Amazon India, the price was extracted as 76606.4 but currency was defaulted to 'Unknown'.
        # Since the store was 'Amazon', is_inr evaluated to False.
        # This applied USD thresholds (max $3000) instead of INR thresholds, falsely rejecting the listing.
        # Fix: The scraper now explicitly extracts 'INR' and passes it.
        valid, reason = is_valid_result("iPhone 16", "Amazon.in : iPhone 16", 76606.4, "Amazon", "INR")
        self.assertTrue(valid, f"Regression failed: falsely rejected valid INR price on Amazon. Reason: {reason}")
    def test_outlier_high_mid_range_inr(self):
        valid, reason = is_valid_result("redmi 13 5g", "Redmi 13 5G", 60000, "Amazon", "INR")
        self.assertFalse(valid)
        self.assertIn("too high", reason)

if __name__ == '__main__':
    unittest.main()