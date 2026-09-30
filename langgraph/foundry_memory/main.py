import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MemorySearchOptions
from azure.identity import DefaultAzureCredential
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.agents.middleware import AzureAIMemoryMiddleware
from _common import build_model, port, require_env

store, scope, endpoint = require_env("MEMORY_STORE_NAME", "MEMORY_SCOPE", "FOUNDRY_PROJECT_ENDPOINT")
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
    store_name=store, scope=scope, project_endpoint=endpoint,
    credential=credential, update_every_n_turns=1,
    roles=["user", "assistant"],
)
graph = create_agent(
    build_model(), tools=[search_memory],
    middleware=[memory],
    system_prompt="Retrieve relevant memories before answering personal-context questions.",
)
if __name__ == "__main__":
    ResponsesHostServer(graph).run(port=port())
