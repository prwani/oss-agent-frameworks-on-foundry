"""Filesystem-grounded agent using Claude's built-in file tools.

This is the one capability where the Claude Agent SDK needs no adapter at all:
Read, Glob, and Grep ship with the CLI. `add_dirs` and `cwd` scope the agent to
DATA_DIR, and write/execute tools are withheld so the sample stays read-only.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)

from _common import build_options, port, prompt_from_context, require_env, run_text

READ_ONLY_TOOLS = ["Read", "Glob", "Grep"]


def data_dir() -> str:
    path = Path(require_env("DATA_DIR")[0]).resolve()
    if not path.is_dir():
        raise RuntimeError(f"DATA_DIR is not a directory: {path}")
    return str(path)


app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    root = data_dir()
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt=(
            f"Answer questions about the files under {root}. "
            "Use Glob and Grep to locate files and Read to inspect them. "
            "Never speculate about contents you have not read."
        ),
        cwd=root,
        add_dirs=[root],
        tools=READ_ONLY_TOOLS,
        allowed_tools=READ_ONLY_TOOLS,
        disallowed_tools=["Write", "Edit", "Bash", "WebFetch", "WebSearch"],
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
