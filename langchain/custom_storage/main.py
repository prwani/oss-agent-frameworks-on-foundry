import asyncio
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langgraph_checkpoint_cosmos.aio import AsyncCosmosDBSaver
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

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

class SQLiteConversationStore:
    """Local SQLite fallback for conversation state."""
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS state (chain_id TEXT, key TEXT, data TEXT NOT NULL, PRIMARY KEY(chain_id,key))")
        self.lock = asyncio.Lock()

    async def get(self, conversation_chain_id: str, key: str):
        async with self.lock:
            with sqlite3.connect(self.path) as db:
                row = db.execute("SELECT data FROM state WHERE chain_id=? AND key=?", (conversation_chain_id,key)).fetchone()
        return json.loads(row[0]) if row else None

    async def set(self, conversation_chain_id: str, key: str, data: dict[str,str]):
        encoded = json.dumps(data)
        async with self.lock:
            with sqlite3.connect(self.path) as db:
                db.execute("INSERT INTO state VALUES(?,?,?) ON CONFLICT(chain_id,key) DO UPDATE SET data=excluded.data", (conversation_chain_id,key,encoded))

load_dotenv()

async def main() -> None:
    use_foundry = os.getenv("USE_FOUNDRY_STORAGE", "false").lower() in ("true", "1", "yes")
    # Check if using SQLite fallback
    use_sqlite = os.getenv("USE_SQLITE_STORAGE", "false").lower() in ("true", "1", "yes")

    if use_foundry:
        log.info("Using Foundry-managed conversation storage")
        graph = create_agent(build_model(), tools=[])
        await ResponsesHostServer(graph).run_async(port=int(os.getenv("PORT", "8088")))
    elif use_sqlite:
        sqlite_path = os.getenv("SQLITE_STORAGE_PATH", "./state/conversations.sqlite")
        log.info(f"Using SQLite storage at {sqlite_path}")
        graph = create_agent(build_model(), tools=[])
        server = ResponsesHostServer(
            graph,
            conversation_chain_store=SQLiteConversationStore(sqlite_path)
        )
        await server.run_async(port=int(os.getenv("PORT", "8088")))
    else:
        # Use Cosmos DB (default)
        log.info("Using Cosmos DB storage")
        async with AsyncCosmosDBSaver.from_conn_info(
            endpoint=required("AZURE_COSMOS_ENDPOINT"),
            credential=DefaultAzureCredential(),
            database_name=required("AZURE_COSMOS_DATABASE_NAME"),
            container_name=required("AZURE_COSMOS_CONTAINER_NAME"),
        ) as checkpointer:
            graph = create_agent(
                build_model(),
                tools=[],
                checkpointer=checkpointer,
                system_prompt="You are a friendly assistant with Cosmos-backed conversation state."
            )
            await ResponsesHostServer(graph).run_async(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    asyncio.run(main())
