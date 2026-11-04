import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.instrumentation.dbapi import instrument_connection
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import main

AUTH = {"Authorization": "Bearer test-token"}
exporter = InMemorySpanExporter()
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))


def traced_fake_connection(user_row):
    conn = MagicMock()
    conn.cursor.return_value.fetchone.return_value = user_row
    conn.cursor.return_value.fetchall.return_value = []
    return instrument_connection("psycopg2", conn, database_system="postgresql")


class RequestTracingTests(unittest.TestCase):
    def setUp(self):
        exporter.clear()
        self.client = TestClient(main.app)
        env = patch.dict(os.environ, {"HEADER_AUTHORIZATION": "test-token"})
        env.start()
        self.addCleanup(env.stop)

    def get_alerts(self, user_row, headers=AUTH):
        with patch("endpoints.alerts.get_db_connection", return_value=traced_fake_connection(user_row)):
            return self.client.get("/alerts", params={"auth0_sub": "auth0|abc"}, headers=headers)

    def spans_by_name(self):
        return {span.name: span for span in exporter.get_finished_spans()}

    def test_query_param_user_id_is_on_request_and_db_spans(self):
        response = self.get_alerts({"name": "A", "email": "a@example.com"})

        self.assertEqual(response.status_code, 200)
        spans = self.spans_by_name()
        self.assertEqual(spans["GET /alerts"].attributes["user.id"], "auth0|abc")
        self.assertEqual(spans["GET /alerts"].attributes["outcome"], "success")
        self.assertEqual(spans["SELECT"].attributes["user.id"], "auth0|abc")

    def test_json_body_user_id_is_read_and_body_still_reaches_handler(self):
        with patch("endpoints.alerts.get_db_connection", return_value=traced_fake_connection(None)):
            response = self.client.post("/alerts", json={"auth0Sub": "auth0|body"}, headers=AUTH)

        self.assertEqual(response.status_code, 404)
        spans = self.spans_by_name()
        self.assertEqual(spans["POST /alerts"].attributes["user.id"], "auth0|body")
        self.assertEqual(spans["POST /alerts"].attributes["outcome"], "rejected")
        self.assertEqual(spans["SELECT"].attributes["user.id"], "auth0|body")

    def test_incoming_traceparent_continues_the_callers_trace(self):
        caller_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        headers = {**AUTH, "traceparent": f"00-{caller_trace_id}-00f067aa0ba902b7-01"}

        self.get_alerts({"name": "A", "email": "a@example.com"}, headers=headers)

        trace_ids = {f"{span.context.trace_id:032x}" for span in exporter.get_finished_spans()}
        self.assertEqual(trace_ids, {caller_trace_id})


if __name__ == "__main__":
    unittest.main()
