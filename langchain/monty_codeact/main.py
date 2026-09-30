from typing import Annotated
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from pydantic_monty import Monty
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI

SCOPE = "https://ai.azure.com/.default"

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def build_model() -> ChatOpenAI:
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=required("FOUNDRY_PROJECT_ENDPOINT"), credential=credential)
    client = project.get_openai_client()
    return ChatOpenAI(
        model=required("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        base_url=str(client.base_url),
        api_key=get_bearer_token_provider(credential, SCOPE),
        streaming=True,
        use_responses_api=True,
        output_version="responses/v1",
    )

load_dotenv()

@tool
def execute_code(code: Annotated[str, "Sandboxed Python expression or statements; finish with an expression to return it."]) -> str:
    """Execute Python in pydantic-monty's isolated runtime without filesystem or network access."""
    with Monty() as pool:
        with pool.checkout() as session:
            return repr(session.feed_run(code))

def main() -> None:
    graph = create_agent(build_model(), tools=[execute_code],
        system_prompt="Use execute_code for multi-step computation. The sandbox has no filesystem, environment, or network access.")
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
