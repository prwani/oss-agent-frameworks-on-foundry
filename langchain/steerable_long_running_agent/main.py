from dotenv import load_dotenv
from azure.ai.agentserver.responses import ResponsesServerOptions
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
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

def main() -> None:
    graph = create_agent(build_model(), tools=[], system_prompt=(
        "When asked to count down, emit one number per line with a unique short remark before each number. "
        "Stop and follow the newest user instruction if the conversation is steered."
    ))
    ResponsesHostServer(
        graph, options=ResponsesServerOptions(steerable_conversations=True)
    ).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
