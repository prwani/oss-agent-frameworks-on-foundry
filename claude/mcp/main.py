"""Connect Claude to a remote MCP server.

MCP is first-class in the Claude Agent SDK: remote servers are declared directly
in `ClaudeAgentOptions.mcp_servers`, so no adapter layer is required.
"""

from __future__ import annotations

import asyncio

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)

from _common import build_options, port, prompt_from_context, require_env, run_text


def mcp_servers() -> dict[str, dict[str, object]]:
    url, token = require_env("MCP_SERVER_URL", "MCP_AUTH_TOKEN")
    return {
        "remote": {
            "type": "http",
            "url": url,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    }


app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt="Answer using the connected MCP server's tools when they apply.",
        mcp_servers=mcp_servers(),
        # Only the declared MCP servers are loaded; filesystem config is ignored.
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
