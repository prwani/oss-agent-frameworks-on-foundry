"""Foundry Toolbox tools combined with SEP-2640 skill resources.

Skills are materialised from the toolbox into the agent workspace so that
Claude's native `skills` option can load them, and toolbox tools remain reachable
through the same MCP bridge used by the `foundry_toolbox` sample.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
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

from _common import build_options, port, prompt_from_context, require_env, run_text, workspace


async def _toolbox_resources(uri: str) -> list[str]:
    endpoint, toolbox_name = require_env("FOUNDRY_PROJECT_ENDPOINT", "TOOLBOX_NAME")
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
            blobs = await client.toolboxes.get_resources(toolbox_name=toolbox_name, uris=uri)
    return [blob.as_string() for blob in blobs or []]


@tool("load_skill", "Load one SEP-2640 skill resource, such as skill://name/SKILL.md.", {"uri": str})
async def load_skill(args: dict[str, Any]) -> dict[str, Any]:
    uri = str(args["uri"])
    try:
        blobs = await _toolbox_resources(uri)
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Skill load failed: {exc}"}], "is_error": True}
    if not blobs:
        return {"content": [{"type": "text", "text": f"No toolbox skill resource found for {uri}"}], "is_error": True}
    return {"content": [{"type": "text", "text": "\n".join(blobs)}]}


skills_server = create_sdk_mcp_server(name="skills", version="1.0.0", tools=[load_skill])


async def skills_index() -> str:
    blobs = await _toolbox_resources("skill://index.json")
    if not blobs:
        raise RuntimeError("Toolbox does not expose skill://index.json")
    return "\n".join(blobs)


def materialise_skills(index_text: str) -> list[str]:
    """Write the skill index into the workspace so it survives across turns."""
    skills_dir = Path(workspace()) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "index.json").write_text(index_text, encoding="utf-8")
    try:
        entries = json.loads(index_text)
    except json.JSONDecodeError:
        return []
    if isinstance(entries, dict):
        entries = entries.get("skills", [])
    return [str(entry.get("name")) for entry in entries if isinstance(entry, dict) and entry.get("name")]


app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    index_text = await skills_index()
    materialise_skills(index_text)
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt=(
            "Available skills index:\n"
            f"{index_text}\n\n"
            "Load a skill with mcp__skills__load_skill before relying on its instructions."
        ),
        mcp_servers={"skills": skills_server},
        allowed_tools=["mcp__skills__load_skill"],
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
