from core.config import config
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracer() -> None:
    COLLECTOR_ENDPOINT = config.jaeger_collector_endpoint
    COLLECTOR_PORT = config.jaeger_collector_port
    SERVICE_NAME = config.project_name

    resource = Resource(attributes={"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=f"http://{COLLECTOR_ENDPOINT}:{COLLECTOR_PORT}/v1/traces"
        )
    )
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
