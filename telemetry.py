"""OpenTelemetry tracing for the API.

Every request becomes a trace. Spans are exported over OTLP only when
OTEL_EXPORTER_OTLP_ENDPOINT is set (Grafana Cloud in production), so local
runs and tests send nothing.
"""

import json
import os
from contextvars import ContextVar

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = "sportsjobs-api"

current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)


class UserIdSpanProcessor(SpanProcessor):
    """Tag every span started during a request with the caller's Auth0 subject."""

    def on_start(self, span, parent_context=None):
        user_id = current_user_id.get()
        if user_id:
            span.set_attribute("user.id", user_id)


def request_outcome(status_code: int) -> str:
    if status_code >= 500:
        return "error"
    if status_code >= 400:
        return "rejected"
    return "success"


async def read_user_id(request: Request) -> str | None:
    """Find the Auth0 subject in the query string or the JSON body."""
    user_id = request.query_params.get("auth0_sub")
    if user_id:
        return user_id
    if not request.headers.get("content-type", "").startswith("application/json"):
        return None
    try:
        body = json.loads(await request.body())
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    user_id = body.get("auth0Sub") or body.get("auth0_sub")
    return user_id if isinstance(user_id, str) else None


async def tag_request_span(request: Request, call_next):
    span = trace.get_current_span()
    user_id = await read_user_id(request)
    if user_id:
        span.set_attribute("user.id", user_id)
    token = current_user_id.set(user_id)
    try:
        response = await call_next(request)
    except Exception:
        span.set_attribute("outcome", "error")
        raise
    finally:
        current_user_id.reset(token)
    span.set_attribute("outcome", request_outcome(response.status_code))
    return response


def setup_tracing(app: FastAPI) -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    provider.add_span_processor(UserIdSpanProcessor())
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    app.middleware("http")(tag_request_span)
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=provider, exclude_spans=["receive", "send"]
    )
