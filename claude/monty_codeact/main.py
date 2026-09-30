"""Sandboxed code execution for Claude.

Claude Code ships a Bash tool, but it executes against the real container
filesystem. To match the bounded-sandbox behaviour of the other framework
columns, built-in execution tools are disabled and a `pydantic-monty` sandbox is
published as an in-process MCP tool instead.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pydantic_monty
from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)
from claude_agent_sdk import create_sdk_mcp_server, tool

from _common import build_options, port, prompt_from_context, run_text

MAX_DURATION_SECS = 3.0
MAX_MEMORY_BYTES = 4 * 1024 * 1024


def _execute(code: str) -> str:
    limits = pydantic_monty.ResourceLimits(
        max_duration_secs=MAX_DURATION_SECS, max_memory=MAX_MEMORY_BYTES
    )
    with pydantic_monty.Monty() as pool:
        with pool.checkout(limits=limits) as session:
            return repr(session.feed_run(code))


@tool(
    "execute_code",
    "Execute a bounded Python expression in a sandbox. No imports or filesystem access.",
    {"code": str},
)
async def execute_code(args: dict[str, Any]) -> dict[str, Any]:
    try:
        output = await asyncio.to_thread(_execute, str(args["code"]))
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Execution failed: {exc}"}], "is_error": True}
    return {"content": [{"type": "text", "text": output}]}


sandbox = create_sdk_mcp_server(name="sandbox", version="1.0.0", tools=[execute_code])

app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt=(
            "Use mcp__sandbox__execute_code for computation and data transformations "
            "rather than doing arithmetic in your head."
        ),
        mcp_servers={"sandbox": sandbox},
        allowed_tools=["mcp__sandbox__execute_code"],
        disallowed_tools=["Bash", "Write", "Edit"],
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
