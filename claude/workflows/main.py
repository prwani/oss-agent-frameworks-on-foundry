"""Multi-stage workflow using Claude Agent SDK subagents.

Claude models delegation through named subagents (`ClaudeAgentOptions.agents`)
rather than an explicit graph. The lead agent is instructed to run the stages in
order, and each subagent carries its own prompt and turn budget.
"""

from __future__ import annotations

import asyncio

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    TextResponse,
)
from claude_agent_sdk import AgentDefinition

from _common import build_options, port, prompt_from_context, run_text

AGENTS = {
    "writer": AgentDefinition(
        description="Writes a single memorable marketing slogan.",
        prompt="Write exactly one memorable slogan for the requested subject. Return only the slogan.",
        tools=[],
        maxTurns=1,
    ),
    "legal": AgentDefinition(
        description="Reviews copy for misleading or unsubstantiated legal claims.",
        prompt=(
            "Review the supplied slogan for misleading or unsubstantiated claims. "
            "If it is problematic, rewrite it so it is defensible. Return only the final slogan."
        ),
        tools=[],
        maxTurns=1,
    ),
    "formatter": AgentDefinition(
        description="Formats approved copy as concise retro terminal art.",
        prompt="Format the supplied slogan as concise retro terminal art. Return only the formatted block.",
        tools=[],
        maxTurns=1,
    ),
}

SYSTEM_PROMPT = (
    "Produce a slogan by delegating through three stages in order: first the 'writer' subagent, "
    "then pass its output to the 'legal' subagent, then pass that output to the 'formatter' subagent. "
    "Return only the formatter's final output."
)

app = ResponsesAgentServerHost()


@app.response_handler
async def handler(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
) -> TextResponse:
    prompt = await prompt_from_context(context)
    options = build_options(
        system_prompt=SYSTEM_PROMPT,
        agents=AGENTS,
        allowed_tools=["Task"],
        tools=["Task"],
        max_turns=12,
    )
    text = await run_text(prompt, options)
    return TextResponse(context, request, text=text)


if __name__ == "__main__":
    app.run(port=port())
