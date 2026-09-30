"""Steerable long-running agent using the bidirectional Claude SDK client.

`ClaudeSDKClient` keeps one CLI session open for the life of the request, which
lets a newer steering turn interrupt work already in flight via `interrupt()`.
The Responses host is started with `steerable_conversations=True` so mid-run user
turns are delivered instead of queued.
"""

from __future__ import annotations

import asyncio

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
    TextResponse,
)
from claude_agent_sdk import ClaudeSDKClient

from _common import build_options, message_text, port, prompt_from_context

SYSTEM_PROMPT = (
    "Count down one integer per line with a unique short remark before each number. "
    "Obey newer steering turns immediately, abandoning the previous count if asked."
)

app = ResponsesAgentServerHost(options=ResponsesServerOptions(steerable_conversations=True))


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(system_prompt=SYSTEM_PROMPT, include_partial_messages=True)

    chunks: list[str] = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            chunks.extend(message_text(message))
            if cancellation_signal.is_set():
                # A newer steering turn arrived; stop the in-flight run promptly.
                await client.interrupt()
                break
    return TextResponse(context, request, text="\n".join(c for c in chunks if c).strip())


if __name__ == "__main__":
    app.run(port=port())
