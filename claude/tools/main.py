"""Custom in-process tools exposed to Claude via an SDK MCP server.

`create_sdk_mcp_server` keeps the tools inside this Python process (no extra
subprocess or network hop). Tools are addressed as `mcp__<server>__<tool>`.
A `can_use_tool` callback gates the command tool so approval is explicit.
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import Any

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)
from claude_agent_sdk import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
    create_sdk_mcp_server,
    tool,
)

from _common import build_options, port, prompt_from_context, run_text

ALLOWED_COMMANDS = {"pwd", "date", "echo"}


@tool("get_weather", "Return demonstration weather for a city", {"location": str})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    location = args["location"]
    return {"content": [{"type": "text", "text": f"The demonstration forecast for {location} is sunny, 21C."}]}


@tool("run_command", "Run an allow-listed local command (pwd, date, or echo TEXT)", {"command": str})
async def run_command(args: dict[str, Any]) -> dict[str, Any]:
    parts = str(args["command"]).split()
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        return {
            "content": [{"type": "text", "text": "Only pwd, date, and echo are allowed."}],
            "is_error": True,
        }
    result = subprocess.run(parts, capture_output=True, text=True, timeout=10, check=False)
    output = (result.stdout + result.stderr).strip() or f"exit_code={result.returncode}"
    return {"content": [{"type": "text", "text": output}]}


toolbox = create_sdk_mcp_server(name="demo", version="1.0.0", tools=[get_weather, run_command])


async def approve(
    tool_name: str,
    tool_input: dict[str, Any],
    context: ToolPermissionContext,
) -> PermissionResultAllow | PermissionResultDeny:
    if tool_name == "mcp__demo__run_command":
        command = str(tool_input.get("command", "")).split()
        if not command or command[0] not in ALLOWED_COMMANDS:
            return PermissionResultDeny(message=f"Command {command!r} is not on the allow list.")
    return PermissionResultAllow()


app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt="Use the provided tools when they are relevant. Explain tool results plainly.",
        mcp_servers={"demo": toolbox},
        allowed_tools=["mcp__demo__get_weather"],
        can_use_tool=approve,
        # "default" lets the permission rules route run_command through `approve`.
        permission_mode="default",
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
