"""Durable long-running work using Claude session resume.

Claude Code writes every session transcript to disk and can resume it by id, so a
long countdown survives a process restart: the session id is persisted per
conversation chain and replayed with `resume`.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
    TextResponse,
)
from claude_agent_sdk import ResultMessage, query

from _common import build_options, message_text, port, prompt_from_context, workspace

SYSTEM_PROMPT = (
    "When asked to count down, emit one integer per line with a short unique remark before each "
    "number. Continue from where the transcript left off if the conversation is resumed."
)


def _session_file() -> Path:
    path = Path(os.environ.get("SESSION_INDEX_PATH", str(Path(workspace()) / "sessions.json")))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_session(chain_id: str) -> str | None:
    path = _session_file()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(chain_id)
    except json.JSONDecodeError:
        return None


def save_session(chain_id: str, session_id: str) -> None:
    path = _session_file()
    try:
        index = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError:
        index = {}
    index[chain_id] = session_id
    path.write_text(json.dumps(index), encoding="utf-8")


app = ResponsesAgentServerHost(options=ResponsesServerOptions(resilient_background=True))


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    chain_id = getattr(context, "conversation_chain_id", None) or "default"
    prompt = await prompt_from_context(context)
    resume = load_session(chain_id)
    options = build_options(
        system_prompt=SYSTEM_PROMPT,
        max_turns=1,
        **({"resume": resume} if resume else {}),
    )

    chunks: list[str] = []
    async for message in query(prompt=prompt, options=options):
        if cancellation_signal.is_set():
            break
        chunks.extend(message_text(message))
        if isinstance(message, ResultMessage) and message.session_id:
            save_session(chain_id, message.session_id)
    return TextResponse(context, request, text="\n".join(c for c in chunks if c).strip())


if __name__ == "__main__":
    app.run(port=port())
