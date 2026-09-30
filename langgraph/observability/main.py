import os
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.callbacks.tracers import enable_auto_tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from _common import build_model, port

def main() -> None:
    if not (os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or os.environ.get("FOUNDRY_PROJECT_ENDPOINT")):
        raise RuntimeError("Configure Foundry endpoint, App Insights, or an OTLP endpoint")
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        enable_auto_tracing()
    else:
        enable_auto_tracing(auto_configure_azure_monitor=True)
    graph = create_agent(build_model(), tools=[])
    ResponsesHostServer(graph).run(port=port())

if __name__ == "__main__":
    main()
