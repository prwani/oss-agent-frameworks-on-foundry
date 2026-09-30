from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.agents.middleware import AzureAIMemoryMiddleware
import json
import os

from azure.ai.projects.models import MemorySearchOptions
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

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
    endpoint = required("FOUNDRY_PROJECT_ENDPOINT")
    store = required("MEMORY_STORE_NAME")
    scope = required("MEMORY_SCOPE")
    credential = DefaultAzureCredential()
    memory_client = AIProjectClient(endpoint=endpoint, credential=credential)

    class TypedAzureAIMemoryMiddleware(AzureAIMemoryMiddleware):
        def _flush_pending_updates(self) -> None:
            if not self._pending_items:
                return
            items = [{"type": "message", **item} for item in self._pending_items]
            poller = self._client.beta.memory_stores.begin_update_memories(
                name=self._store_name,
                scope=self._scope,
                items=items,
                previous_update_id=self._previous_update_id,
                update_delay=self._update_delay,
            )
            poller.result()
            self._previous_update_id = getattr(poller, "update_id", None)
            self._pending_items = []
            self._pending_turns = 0

    @tool
    def search_memory(query: str) -> str:
        """Search long-term memory for relevant user context."""
        result = memory_client.beta.memory_stores.search_memories(
            name=store,
            scope=scope,
            items=[{"type": "message", "role": "user", "content": query}],
            options=MemorySearchOptions(max_memories=5),
        )
        return json.dumps([entry.as_dict() for entry in result.memories], default=str)

    memory = TypedAzureAIMemoryMiddleware(
        store_name=store,
        scope=scope,
        roles=["user", "assistant"],
        project_endpoint=endpoint,
        credential=credential,
    )
    graph = create_agent(
        build_model(),
        tools=[search_memory],
        middleware=[memory],
        system_prompt="Remember useful user facts and retrieve memories when relevant.",
    )
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
