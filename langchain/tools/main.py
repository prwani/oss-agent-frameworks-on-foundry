"""Local tools, including a human-approved side-effecting command tool."""
import asyncio
import os
import shlex
import subprocess
from random import choice, randint
from typing import Annotated

from azure.ai.agentserver.core import AgentConfig
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_azure_ai.agents.hosting import FoundryCheckpointSaver, ResponsesHostServer
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

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
def get_weather(location: Annotated[str, "City and country."]) -> str:
    """Return simulated current weather for a location."""
    return (
        f"Weather in {location}: {choice(['sunny', 'cloudy', 'rainy'])}, "
        f"high {randint(10, 30)}C."
    )


@tool
def run_command(command: Annotated[str, "Command and arguments, without shell syntax."]) -> str:
    """Run a local command after explicit human approval."""
    result = subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\nexit_code: {result.returncode}"


class ApprovalResponsesHostServer(ResponsesHostServer):
    async def build_resume_command(self, request, context, pending):
        command, consumed = await super().build_resume_command(
            request, context, pending
        )
        if (
            command is not None
            and isinstance(command.resume, dict)
            and "action_requests" in command.resume
        ):
            command = Command(
                resume={
                    "decisions": [
                        {"type": "approve"}
                        for _ in command.resume["action_requests"]
                    ]
                },
                update=command.update,
                goto=command.goto,
            )
        return command, consumed


async def main() -> None:
    checkpointer = (
        FoundryCheckpointSaver(user_isolation=True)
        if AgentConfig.from_env().is_hosted
        else InMemorySaver()
    )
    async with checkpointer:
        graph = create_agent(
            build_model(),
            tools=[get_weather, run_command],
            middleware=[
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "get_weather": False,
                        "run_command": {
                            "allowed_decisions": ["approve", "edit", "reject"]
                        },
                    }
                )
            ],
            checkpointer=checkpointer,
            system_prompt="Use tools when relevant. Never claim a command ran before its result is returned.",
        )
        await ApprovalResponsesHostServer(graph).run_async(
            port=int(os.getenv("PORT", "8088"))
        )


if __name__ == "__main__":
    asyncio.run(main())
