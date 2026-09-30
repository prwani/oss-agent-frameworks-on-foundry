"""Long-term memory backed by a Foundry Memory store.

The Claude Agent SDK has no memory-provider lifecycle, so recall and capture are
driven explicitly: a retrieval MCP tool lets the model search the store, and the
handler writes each completed turn back after responding.
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
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MemorySearchOptions
from azure.identity import DefaultAzureCredential
from claude_agent_sdk import create_sdk_mcp_server, tool

from _common import build_options, port, request_messages, messages_to_prompt, require_env, run_text

STORE, SCOPE, ENDPOINT = require_env("MEMORY_STORE_NAME", "MEMORY_SCOPE", "FOUNDRY_PROJECT_ENDPOINT")
_credential = DefaultAzureCredential()
_client = AIProjectClient(endpoint=ENDPOINT, credential=_credential)


def _search(query: str) -> list[dict[str, Any]]:
    result = _client.beta.memory_stores.search_memories(
        name=STORE,
        scope=SCOPE,
        items=[{"type": "message", "role": "user", "content": query}],
        options=MemorySearchOptions(max_memories=5),
    )
    return [entry.as_dict() for entry in result.memories]


def _remember(items: list[dict[str, str]]) -> None:
    poller = _client.beta.memory_stores.begin_update_memories(
        name=STORE,
        scope=SCOPE,
        items=[{"type": "message", **item} for item in items],
    )
    poller.result()


@tool("search_memory", "Search long-term memory for relevant user context.", {"query": str})
async def search_memory(args: dict[str, Any]) -> dict[str, Any]:
    try:
        memories = await asyncio.to_thread(_search, str(args["query"]))
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Memory search failed: {exc}"}], "is_error": True}
    text = json.dumps(memories, default=str) if memories else "No relevant memories were found."
    return {"content": [{"type": "text", "text": text}]}


memory_server = create_sdk_mcp_server(name="memory", version="1.0.0", tools=[search_memory])

app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    messages = await request_messages(context)
    prompt = messages_to_prompt(messages)
    options = build_options(
        system_prompt=(
            "Call mcp__memory__search_memory before answering questions that depend on personal "
            "context, then answer using what you recall."
        ),
        mcp_servers={"memory": memory_server},
        allowed_tools=["mcp__memory__search_memory"],
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)

    turn = [message for message in messages if message["role"] == "user"][-1:]
    if turn:
        turn.append({"role": "assistant", "content": text})
        try:
            await asyncio.to_thread(_remember, turn)
        except Exception:
            # Memory capture is best-effort and must not fail the response.
            pass
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
