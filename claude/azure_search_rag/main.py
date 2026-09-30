"""Retrieval-augmented generation over an existing Azure AI Search index.

The Claude Agent SDK has no built-in Azure AI Search integration, so retrieval is
published as an in-process MCP tool backed by the Azure Search SDK.
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
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from claude_agent_sdk import create_sdk_mcp_server, tool

from _common import build_options, port, prompt_from_context, require_env, run_text

MAX_RESULTS = 5


@tool(
    "search",
    "Search the configured Azure AI Search index and return the most relevant documents.",
    {"query": str},
)
async def search(args: dict[str, Any]) -> dict[str, Any]:
    endpoint, index_name = require_env("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_INDEX_NAME")
    try:
        async with DefaultAzureCredential() as credential:
            async with SearchClient(endpoint=endpoint, index_name=index_name, credential=credential) as client:
                documents = []
                async for result in await client.search(str(args["query"]), top=MAX_RESULTS):
                    documents.append({k: v for k, v in result.items() if not k.startswith("@")})
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"Search failed: {exc}"}], "is_error": True}
    if not documents:
        return {"content": [{"type": "text", "text": "No matching documents were found."}]}
    return {"content": [{"type": "text", "text": json.dumps(documents, default=str, indent=2)}]}


retrieval = create_sdk_mcp_server(name="retrieval", version="1.0.0", tools=[search])

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
            "Answer strictly from the indexed corpus. Always call mcp__retrieval__search first, "
            "cite the documents you used, and say so plainly when the index has no answer."
        ),
        mcp_servers={"retrieval": retrieval},
        allowed_tools=["mcp__retrieval__search"],
        strict_mcp_config=True,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
