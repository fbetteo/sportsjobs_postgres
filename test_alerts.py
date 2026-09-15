import unittest
import asyncio
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from endpoints.alerts import add_alert, alert_signature, delete_alert
from models.schemas import AddAlert, CreateAlert


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

    def test_delete_scopes_alert_to_authenticated_users_email(self):
        class FakeCursor:
            def __init__(self):
                self.calls = []
                self.rows = iter([
                    {"name": "Alex", "email": "Alex@Example.com"},
                    None,
                ])

            def execute(self, query, params):
                self.calls.append((query, params))

            def fetchone(self):
                return next(self.rows)

            def close(self):
                pass

        class FakeConnection:
            def __init__(self):
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self, **_kwargs):
                return self.cursor_instance

            def commit(self):
                self.committed = True

            def rollback(self):
                pass

            def close(self):
                pass

        conn = FakeConnection()
        request = Request({"type": "http", "headers": [(b"authorization", b"Bearer test-token")]})
        with patch.dict("os.environ", {"HEADER_AUTHORIZATION": "test-token"}), patch(
            "endpoints.alerts.get_db_connection", return_value=conn
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(delete_alert(9, "auth0|alex", request))

        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(conn.cursor_instance.calls[0][1], ("auth0|alex",))
        self.assertEqual(conn.cursor_instance.calls[1][1], (9, "alex@example.com"))
        self.assertFalse(conn.committed)

    def test_create_uses_backend_users_email_instead_of_submitted_email(self):
        class FakeCursor:
            def __init__(self):
                self.calls = []
                self.rows = iter([
                    {"name": "Alex", "email": "Login@Example.com"},
                    {"alert_id": 5, "email": "login@example.com"},
                ])

            def execute(self, query, params):
                self.calls.append((query, params))

            def fetchone(self):
                return next(self.rows)

            def fetchall(self):
                return []

            def close(self):
                pass

        class FakeConnection:
            def __init__(self):
                self.cursor_instance = FakeCursor()
                self.committed = False

            def cursor(self, **_kwargs):
                return self.cursor_instance

            def commit(self):
                self.committed = True

            def rollback(self):
                pass

            def close(self):
                pass

        conn = FakeConnection()
        request = Request({"type": "http", "headers": [(b"authorization", b"Bearer test-token")]})
        record = CreateAlert.model_validate({
            "auth0Sub": "auth0|alex", "email": "someone-else@example.com", "country": ["Canada"],
        })
        with patch.dict("os.environ", {"HEADER_AUTHORIZATION": "test-token"}), patch(
            "endpoints.alerts.get_db_connection", return_value=conn
        ):
            result = asyncio.run(add_alert(record, request))

        self.assertEqual(result["record"]["email"], "login@example.com")
        self.assertEqual(conn.cursor_instance.calls[1][1], ("login@example.com",))
        self.assertEqual(conn.cursor_instance.calls[3][1][1], "login@example.com")
        self.assertTrue(conn.committed)


if __name__ == "__main__":
    unittest.main()
