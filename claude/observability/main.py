"""Tracing for a Claude Agent SDK agent.

Two layers are instrumented:

1. The Python host process, via OpenTelemetry (Azure Monitor or a generic OTLP
   collector).
2. The Claude Code subprocess, via its own OpenTelemetry environment variables,
   which are forwarded through `ClaudeAgentOptions.env`.
"""

from __future__ import annotations

import asyncio
import os

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)
from opentelemetry import trace

from _common import build_options, foundry_env, port, prompt_from_context, run_text


def configure_tracing() -> None:
    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not connection_string and not otlp_endpoint:
        raise RuntimeError(
            "Set APPLICATIONINSIGHTS_CONNECTION_STRING or OTEL_EXPORTER_OTLP_ENDPOINT "
            "to enable tracing for this sample."
        )
    if connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=connection_string)
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)


def cli_telemetry_env() -> dict[str, str]:
    """Turn on Claude Code's own OpenTelemetry export inside the subprocess."""
    env = foundry_env()
    env["CLAUDE_CODE_ENABLE_TELEMETRY"] = "1"
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        env["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
        env["OTEL_METRICS_EXPORTER"] = "otlp"
        env["OTEL_LOGS_EXPORTER"] = "otlp"
    return env


configure_tracing()
tracer = trace.get_tracer(__name__)
app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    with tracer.start_as_current_span("claude.responses.handler") as span:
        prompt = await prompt_from_context(context)
        span.set_attribute("claude.prompt_chars", len(prompt))
        options = build_options(
            system_prompt="You are a concise, helpful assistant.",
            env=cli_telemetry_env(),
            max_turns=1,
        )
        text = await run_text(prompt, options)
        span.set_attribute("claude.response_chars", len(text))
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
