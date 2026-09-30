import json
from typing import Annotated
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port, require_env

endpoint, index_name = require_env("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_INDEX_NAME")
client = SearchClient(endpoint, index_name, DefaultAzureCredential())
@tool
def search_knowledge(query: Annotated[str, "Natural-language search query"]) -> str:
    """Search the configured Azure AI Search index and return grounded passages."""
    fields = [x.strip() for x in __import__("os").environ.get("AZURE_SEARCH_SELECT", "content,sourceName,sourceLink").split(",")]
    results = client.search(query, top=3, select=fields)
    return json.dumps([{k: item.get(k) for k in fields} for item in results], default=str)

if __name__ == "__main__":
    graph = create_agent(build_model(), tools=[search_knowledge], system_prompt="Use search_knowledge for factual answers and cite sourceLink.")
    ResponsesHostServer(graph).run(port=port())
