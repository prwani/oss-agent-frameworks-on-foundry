import asyncio
from pathlib import Path
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

def load_skills() -> str:
    files = sorted((Path(__file__).parent / "skills").glob("*/SKILL.md"))
    if not files:
        raise RuntimeError("No skills/*/SKILL.md files were packaged")
    return "\n\n".join(path.read_text() for path in files)

async def load_tools():
    tools = await AzureAIProjectToolbox(toolbox_name=required("TOOLBOX_NAME")).get_tools()
    if not tools:
        raise RuntimeError("The configured toolbox returned no MCP tools")
    return tools

def main() -> None:
    prompt = "Follow these packaged Agent Skills when applicable:\n\n" + load_skills()
    graph = create_agent(build_model(), tools=asyncio.run(load_tools()), system_prompt=prompt)
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
