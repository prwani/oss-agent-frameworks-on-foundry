"""Durable background Responses agent with crash/restart recovery."""
from __future__ import annotations

import asyncio
import os
import signal
from typing import Annotated

from azure.ai.agentserver.core import AgentConfig
from azure.ai.agentserver.responses import ResponsesServerOptions
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_azure_ai.agents.hosting import FoundryCheckpointSaver, ResponsesHostServer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

load_dotenv()
SCOPE = "https://ai.azure.com/.default"


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_model() -> ChatOpenAI:
    credential = DefaultAzureCredential()
    project = AIProjectClient(
        endpoint=required("FOUNDRY_PROJECT_ENDPOINT"), credential=credential
    )
    client = project.get_openai_client()
    return ChatOpenAI(
        model=required("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        base_url=str(client.base_url),
        api_key=get_bearer_token_provider(credential, SCOPE),
        streaming=True,
        use_responses_api=True,
        output_version="responses/v1",
    )


@tool
async def slow_countdown(
    start: Annotated[int, "Positive integer to count down from."],
) -> list[int]:
    """Count down slowly to demonstrate a long-running resumable tool."""
    if start <= 0:
        raise ValueError("start must be positive")
    values = []
    for value in range(start, 0, -1):
        await asyncio.sleep(1)
        values.append(value)
    return values


@tool
async def simulate_crash(config: RunnableConfig) -> str:
    """Crash only when explicitly requested, allowing checkpoint recovery testing."""
    context = config.get("configurable", {}).get("response_context")
    if getattr(context, "is_recovery", False):
        return "Recovered the pending tool call after process restart."
    os.kill(os.getpid(), getattr(signal, "SIGKILL", signal.SIGTERM))
    await asyncio.sleep(3600)
    return "unreachable"


async def main() -> None:
    checkpointer_context = (
        FoundryCheckpointSaver(
            store_name_prefix="langchain/resilient-long-running",
            user_isolation=True,
        )
        if AgentConfig.from_env().is_hosted
        else AsyncSqliteSaver.from_conn_string("checkpoints.sqlite")
    )
    async with checkpointer_context as checkpointer:
        graph = create_agent(
            build_model(),
            tools=[slow_countdown, simulate_crash],
            checkpointer=checkpointer,
            system_prompt=(
                "Use slow_countdown for countdown requests. Call simulate_crash only "
                "when explicitly asked. Briefly report progress and final results."
            ),
        )
        options = ResponsesServerOptions(
            resilient_background=True,
            steerable_conversations=os.getenv(
                "STEERABLE_CONVERSATIONS", "false"
            ).lower()
            in {"1", "true", "yes"},
        )
        await ResponsesHostServer(graph, options=options).run_async(
            port=int(os.getenv("PORT", "8088"))
        )


if __name__ == "__main__":
    asyncio.run(main())
