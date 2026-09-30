"""Expose a Foundry Toolbox to Claude through an SDK MCP bridge.

The Claude Agent SDK has no native Foundry Toolbox client, so this sample uses an
adapter: Foundry Toolbox tools are discovered with the Azure AI Projects SDK and
re-published as in-process MCP tools that Claude can call.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from claude_agent_sdk import create_sdk_mcp_server, tool

from _common import build_options, port, prompt_from_context, require_env, run_text

_PROJECT_SCOPE = "https://ai.azure.com/.default"


async def _invoke_toolbox(tool_name: str, arguments: dict[str, Any]) -> str:
    """Call a single Foundry Toolbox tool and return its result as text."""
    endpoint, toolbox_name = require_env("FOUNDRY_PROJECT_ENDPOINT", "TOOLBOX_NAME")
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
            result = await client.toolboxes.invoke_tool(
                toolbox_name=toolbox_name,
                tool_name=tool_name,
                arguments=arguments,
            )
    return result if isinstance(result, str) else json.dumps(result, default=str)


@tool(
    "invoke",
    "Invoke a tool published by the configured Foundry Toolbox. "
    "Pass the tool name and a JSON object of arguments.",
    {"tool_name": str, "arguments_json": str},
)
async def invoke(args: dict[str, Any]) -> dict[str, Any]:
    try:
        arguments = json.loads(args.get("arguments_json") or "{}")
    except json.JSONDecodeError as exc:
        return {"content": [{"type": "text", "text": f"arguments_json is not valid JSON: {exc}"}], "is_error": True}
    try:
        output = await _invoke_toolbox(str(args["tool_name"]), arguments)
    except Exception as exc:  # surfaced to the model so it can recover
        return {"content": [{"type": "text", "text": f"Toolbox call failed: {exc}"}], "is_error": True}
    return {"content": [{"type": "text", "text": output}]}


toolbox_bridge = create_sdk_mcp_server(name="foundry_toolbox", version="1.0.0", tools=[invoke])

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
            "You can reach Foundry Toolbox tools through mcp__foundry_toolbox__invoke. "
            "Pass arguments as a JSON object string."
        ),
        mcp_servers={"foundry_toolbox": toolbox_bridge},
        allowed_tools=["mcp__foundry_toolbox__invoke"],
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
