import asyncio, json, sqlite3
import os
from pathlib import Path
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port, require_env

class SQLiteConversationStore:
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

if __name__ == "__main__":
    graph = create_agent(build_model(), tools=[])
    if os.getenv("USE_FOUNDRY_STORAGE", "false").lower() in ("true", "1", "yes"):
        ResponsesHostServer(graph).run(port=port())
    else:
        path = require_env("SQLITE_STORAGE_PATH")[0]
        ResponsesHostServer(graph, conversation_chain_store=SQLiteConversationStore(path)).run(port=port())
