import json
from typing import Annotated
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
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

credential = DefaultAzureCredential()

@tool
def search_knowledge_base(query: Annotated[str, "Natural-language support question."]) -> str:
    """Retrieve grounded documents from the configured Azure AI Search index."""
    client = SearchClient(
        endpoint=required("AZURE_SEARCH_ENDPOINT"),
        index_name=required("AZURE_SEARCH_INDEX_NAME"),
        credential=credential,
    )
    fields = [field.strip() for field in os.getenv(
        "AZURE_SEARCH_SELECT", "content,sourceName,sourceLink"
    ).split(",") if field.strip()]
    kwargs = {"search_text": query, "top": 3, "select": fields}
    semantic = os.getenv("AZURE_SEARCH_SEMANTIC_CONFIGURATION")
    if semantic:
        kwargs.update(query_type="semantic", semantic_configuration_name=semantic)
    results = [{field: doc.get(field) for field in fields} for doc in client.search(**kwargs)]
    return json.dumps(results)

def main() -> None:
    required("AZURE_SEARCH_ENDPOINT"); required("AZURE_SEARCH_INDEX_NAME")
    graph = create_agent(build_model(), tools=[search_knowledge_base],
        system_prompt="Search before answering factual support questions and cite any available source metadata.")
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
