from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.callbacks.tracers import enable_auto_tracing
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
    if not (os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING") or
            os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv("FOUNDRY_PROJECT_ENDPOINT")):
        raise RuntimeError("Configure APPLICATION_INSIGHTS_CONNECTION_STRING, OTEL_EXPORTER_OTLP_ENDPOINT, or FOUNDRY_PROJECT_ENDPOINT")
    enable_auto_tracing(auto_configure_azure_monitor=not bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")))
    graph = create_agent(build_model(), tools=[], system_prompt="You are a concise observability demo assistant.")
    ResponsesHostServer(
        graph,
        applicationinsights_connection_string=os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING"),
    ).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
