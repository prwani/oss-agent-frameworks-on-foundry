"""Minimal Claude Agent SDK agent served over the Foundry Responses protocol."""

from __future__ import annotations

import asyncio

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)

from _common import build_options, port, prompt_from_context, run_text

SYSTEM_PROMPT = "You are a concise, helpful assistant. Answer directly and accurately."

app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(system_prompt=SYSTEM_PROMPT, max_turns=1)
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
