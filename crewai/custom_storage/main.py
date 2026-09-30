import asyncio
import datetime
import uuid
import json
import sqlite3
import os
import logging
from pathlib import Path
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from common import kickoff_single,request_messages,require_env

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv()
app = ResponsesAgentServerHost()

# Lazy-initialize clients and config
_cosmos_client = None
_sqlite_db = None
_config = None
_use_sqlite = None
_use_foundry = None

def get_sqlite_db():
    global _sqlite_db
    if _sqlite_db is None:
        sqlite_path = _config.get("SQLITE_STORAGE_PATH", "./state/conversations.sqlite")
        path = Path(sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _sqlite_db = sqlite_path
        with sqlite3.connect(_sqlite_db) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    chain_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    input TEXT,
                    output TEXT
                )
            """)
    return _sqlite_db

def get_cosmos_client():
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosClient(_config["COSMOS_ENDPOINT"], credential=DefaultAzureCredential())
    return _cosmos_client

def run_sqlite(messages, user, chain):
    sqlite_path = get_sqlite_db()
    with sqlite3.connect(sqlite_path) as db:
        rows = list(db.execute(
            "SELECT input, output FROM conversations WHERE user_id=? AND chain_id=? ORDER BY created_at DESC LIMIT 20",
            (user, chain)
        ))
        prior = "\n".join(f"user: {r[0]}\nassistant: {r[1]}" for r in reversed(rows))

    answer = kickoff_single(
        messages,
        role="Persistent assistant",
        goal="Continue the stored conversation accurately",
        backstory="A CrewAI assistant with SQLite-backed turn storage.",
        context="STORED TURNS:\n"+prior
    )

    with sqlite3.connect(sqlite_path) as db:
        db.execute(
            "INSERT INTO conversations (id, user_id, chain_id, created_at, input, output) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), user, chain, datetime.datetime.now(datetime.UTC).isoformat(),
             messages[-1]['content'] if messages else '', answer)
        )

    return answer

def run_cosmos(messages, user, chain):
    client = get_cosmos_client()
    container = client.get_database_client(_config["COSMOS_DATABASE_NAME"]).get_container_client(_config["COSMOS_CONTAINER_NAME"])

    rows = list(container.query_items(
        "SELECT TOP 20 * FROM c WHERE c.user_id=@u AND c.chain_id=@c ORDER BY c.created_at",
        parameters=[{"name":"@u","value":user},{"name":"@c","value":chain}],
        partition_key=user
    ))
    prior = "\n".join(f"user: {r['input']}\nassistant: {r['output']}" for r in rows)

    answer = kickoff_single(
        messages,
        role="Persistent assistant",
        goal="Continue the stored conversation accurately",
        backstory="A CrewAI assistant with Cosmos-backed turn storage.",
        context="CUSTOM STORED TURNS:\n"+prior
    )

    container.upsert_item({
        "id": str(uuid.uuid4()),
        "user_id": user,
        "chain_id": chain,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "input": messages[-1]['content'] if messages else '',
        "output": answer
    })

    return answer

@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
    global _config, _use_foundry, _use_sqlite

    if _config is None:
        # Determine storage backend on first request
        _use_foundry = os.getenv("USE_FOUNDRY_STORAGE", "false").lower() in ("true", "1", "yes")
        _use_sqlite = os.getenv("USE_SQLITE_STORAGE", "false").lower() in ("true", "1", "yes")

        if _use_foundry:
            _config = {}
            log.info("Using Foundry-managed conversation storage")
        elif _use_sqlite:
            _config = {"SQLITE_STORAGE_PATH": os.getenv("SQLITE_STORAGE_PATH", "./state/conversations.sqlite")}
            log.info("Using SQLite storage for custom_storage")
        else:
            _config = require_env("COSMOS_ENDPOINT","COSMOS_DATABASE_NAME","COSMOS_CONTAINER_NAME")
            log.info("Using Cosmos DB for custom_storage")

    user = context.platform_context.user_id_key
    if not user:
        user = os.getenv("LOCAL_TEST_USER_ID")
    if not user:
        raise RuntimeError(
            "A platform user ID is required; set LOCAL_TEST_USER_ID only for local testing."
        )

    messages = await request_messages(context)

    if _use_foundry:
        text = await asyncio.to_thread(
            kickoff_single,
            messages,
            role="Persistent assistant",
            goal="Continue the platform-managed conversation accurately",
            backstory="A CrewAI assistant using Foundry-managed conversation history.",
        )
    elif _use_sqlite:
        text = await asyncio.to_thread(run_sqlite, messages, user, context.conversation_chain_id)
    else:
        text = await asyncio.to_thread(run_cosmos, messages, user, context.conversation_chain_id)

    return TextResponse(context, request, text=text)

if __name__=="__main__":
    app.run()
