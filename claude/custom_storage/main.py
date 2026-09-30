"""Mirror Claude session transcripts into custom storage.

The Claude Agent SDK exposes a `SessionStore` protocol: the CLI still writes
transcripts to local disk, and the adapter receives a secondary copy. That makes
sessions recoverable even when container-local disk is not durable.

Only `append` and `load` are required, and the SDK duck-types the adapter rather
than checking `isinstance`.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)

from _common import build_options, port, prompt_from_context, require_env, run_text


class SQLiteSessionStore:
    """Append-only transcript mirror backed by SQLite."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS entries ("
                "project_key TEXT NOT NULL, session_id TEXT NOT NULL, subpath TEXT NOT NULL DEFAULT '', "
                "seq INTEGER NOT NULL, uuid TEXT, data TEXT NOT NULL, "
                "PRIMARY KEY (project_key, session_id, subpath, seq))"
            )
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS entries_uuid "
                "ON entries (project_key, session_id, subpath, uuid) WHERE uuid IS NOT NULL"
            )
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(key: dict[str, Any]) -> tuple[str, str, str]:
        return key["project_key"], key["session_id"], key.get("subpath", "")

    def _append(self, key: dict[str, Any], entries: list[dict[str, Any]]) -> None:
        project_key, session_id, subpath = self._key(key)
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT COALESCE(MAX(seq), -1) FROM entries "
                "WHERE project_key=? AND session_id=? AND subpath=?",
                (project_key, session_id, subpath),
            ).fetchone()
            seq = int(row[0]) + 1
            for entry in entries:
                # `uuid` is the SDK's idempotency key; entries without one are plain appends.
                db.execute(
                    "INSERT OR IGNORE INTO entries VALUES (?,?,?,?,?,?)",
                    (project_key, session_id, subpath, seq, entry.get("uuid"), json.dumps(entry)),
                )
                seq += 1

    def _load(self, key: dict[str, Any]) -> list[dict[str, Any]] | None:
        project_key, session_id, subpath = self._key(key)
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                "SELECT data FROM entries WHERE project_key=? AND session_id=? AND subpath=? ORDER BY seq",
                (project_key, session_id, subpath),
            ).fetchall()
        return [json.loads(row[0]) for row in rows] if rows else None

    async def append(self, key: dict[str, Any], entries: list[dict[str, Any]]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._append, key, entries)

    async def load(self, key: dict[str, Any]) -> list[dict[str, Any]] | None:
        async with self._lock:
            return await asyncio.to_thread(self._load, key)


def build_store() -> SQLiteSessionStore | None:
    if os.getenv("USE_FOUNDRY_STORAGE", "false").lower() in ("true", "1", "yes"):
        # Foundry-managed state is durable, so no external mirror is needed.
        return None
    return SQLiteSessionStore(require_env("SQLITE_STORAGE_PATH")[0])


store = build_store()
app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt="You are a concise, helpful assistant.",
        max_turns=1,
        **({"session_store": store, "session_store_flush": "eager"} if store else {}),
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
