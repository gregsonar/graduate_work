from uuid import uuid4
from fastapi import Request
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from logging import getLogger


class RequestTracker:

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.propagator = TraceContextTextMapPropagator()
        self.logger = getLogger(__name__)

    def get_or_generate_request_id(self, request: Request) -> str:
        request_id = request.headers.get('X-Request-Id')
        if not request_id:
            request_id = str(uuid4())
        return request_id

    def setup_tracing(self, request: Request, request_id: str) -> None:

        context = self.propagator.extract(carrier=dict(request.headers))

        with self.tracer.start_as_current_span(
                f"{request.method} {request.url.path}",
                context=context,
                kind=trace.SpanKind.SERVER,
        ) as span:
            span.set_attribute("request_id", request_id)
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.target", request.url.path)
