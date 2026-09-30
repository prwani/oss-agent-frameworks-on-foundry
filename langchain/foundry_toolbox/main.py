import asyncio
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.tools import AzureAIProjectToolbox
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

async def load_tools():
    tools = await AzureAIProjectToolbox(toolbox_name=required("TOOLBOX_NAME")).get_tools()
    if not tools:
        raise RuntimeError("The configured Foundry Toolbox returned no tools")
    return tools

def main() -> None:
    graph = create_agent(build_model(), tools=asyncio.run(load_tools()),
                         system_prompt="Use Foundry Toolbox tools when relevant.")
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
