import unittest

from endpoints.alerts import alert_signature
from models.schemas import AddAlert


class AddAlertNormalizationTests(unittest.TestCase):
    def test_normalizes_email_and_filter_arrays(self):
        alert = AddAlert.model_validate(
            {
                "name": "  Alex  ",
                "email": " Alex@Example.com ",
                "country": ["Canada", " canada ", "United States"],
                "seniority": None,
            }
        )
        self.assertEqual(alert.name, "Alex")
        self.assertEqual(alert.email, "alex@example.com")
        self.assertEqual(alert.country, ["Canada", "United States"])
        self.assertEqual(alert.seniority, [])

    def test_signature_treats_null_empty_order_and_case_as_identical(self):
        left = {
            "email": "alex@example.com",
            "country": ["Canada", "United States"],
            "seniority": None,
            "industry": ["Sports"],
        }
        right = {
            "email": "ALEX@example.com",
            "country": ["united states", "canada"],
            "seniority": [],
            "industry": ["sports"],
        }
        self.assertEqual(alert_signature(left), alert_signature(right))


if __name__ == "__main__":
    unittest.main()
