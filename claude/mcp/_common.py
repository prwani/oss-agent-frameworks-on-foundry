"""Shared helpers for running the Claude Agent SDK behind the Foundry Responses protocol.

The Claude Agent SDK is a thin Python wrapper around the bundled Claude Code CLI,
which it spawns as a subprocess and drives over newline-delimited JSON. Model
routing is therefore configured through environment variables that are forwarded
to that subprocess rather than through a Python client object.

Claude Code has first-class support for Claude models deployed in Microsoft
Foundry via ``CLAUDE_CODE_USE_FOUNDRY``. Note that this targets the *account*
level Anthropic endpoint (``https://<resource>.services.ai.azure.com/anthropic/v1``)
and the ``https://cognitiveservices.azure.com/.default`` Entra scope, which both
differ from the project-scoped OpenAI-compatible endpoint the other frameworks in
this repository use.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from azure.identity import DefaultAzureCredential
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    CLINotFoundError,
    ResultError,
    ResultMessage,
    TextBlock,
    query,
)
from dotenv import load_dotenv

load_dotenv()

# Claude models in Foundry are served from the Cognitive Services data plane, not
# the ai.azure.com project plane used by the other framework columns.
FOUNDRY_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"

_credential: DefaultAzureCredential | None = None


def require_env(*names: str) -> list[str]:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
    return [os.environ[name] for name in names]


def port() -> int:
    return int(os.environ.get("PORT", "8088"))


def model_name() -> str:
    """Name of the Claude deployment in Foundry (for example a Sonnet deployment)."""
    return require_env("CLAUDE_MODEL_DEPLOYMENT_NAME")[0]


def foundry_target() -> dict[str, str]:
    """Select exactly one of the mutually exclusive Foundry target variables.

    Claude Code rejects `ANTHROPIC_FOUNDRY_BASE_URL` and
    `ANTHROPIC_FOUNDRY_RESOURCE` being set together, and `ClaudeAgentOptions.env`
    is merged *over* the parent environment rather than replacing it. The unused
    variable is therefore blanked explicitly so an inherited value cannot
    reintroduce the conflict.
    """
    base_url = os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")
    resource = os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE")
    if base_url:
        return {"ANTHROPIC_FOUNDRY_BASE_URL": base_url.rstrip("/"), "ANTHROPIC_FOUNDRY_RESOURCE": ""}
    if resource:
        return {"ANTHROPIC_FOUNDRY_RESOURCE": resource, "ANTHROPIC_FOUNDRY_BASE_URL": ""}
    raise RuntimeError(
        "Set ANTHROPIC_FOUNDRY_RESOURCE (or ANTHROPIC_FOUNDRY_BASE_URL) to target your Foundry resource."
    )


def _access_token() -> str:
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    # azure-identity caches the token internally and refreshes it near expiry, so
    # calling this per request keeps long-lived hosts from serving a stale token.
    return _credential.get_token(FOUNDRY_TOKEN_SCOPE).token


def workspace() -> str:
    """Writable directory the CLI subprocess uses as its working directory."""
    path = Path(os.environ.get("CLAUDE_AGENT_WORKSPACE", "/tmp/claude-agent-workspace"))
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def foundry_env() -> dict[str, str]:
    """Environment forwarded to the Claude Code subprocess to target Foundry."""
    deployment = model_name()
    env = {
        "CLAUDE_CODE_USE_FOUNDRY": "1",
        # Aliases such as "sonnet" otherwise resolve to Claude Code's own default
        # Foundry model name, which will not match a custom deployment name.
        "ANTHROPIC_DEFAULT_SONNET_MODEL": deployment,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": deployment,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": deployment,
        # Keep transcripts inside the writable workspace instead of $HOME.
        "CLAUDE_CONFIG_DIR": str(Path(workspace()) / ".claude"),
    }
    env.update(foundry_target())
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
    if api_key:
        env["ANTHROPIC_FOUNDRY_API_KEY"] = api_key
    else:
        env["ANTHROPIC_FOUNDRY_AUTH_TOKEN"] = _access_token()
    return env


def build_options(**overrides: Any) -> ClaudeAgentOptions:
    """Build options pinned to the Foundry backend.

    Call this per request so the Entra bearer token is refreshed.
    """
    params: dict[str, Any] = {
        "model": model_name(),
        "env": foundry_env(),
        "cwd": workspace(),
        # Ignore user/project settings files so hosted runs are reproducible.
        "setting_sources": [],
        "permission_mode": "bypassPermissions",
        "tools": [],
        "max_turns": 8,
    }
    params.update(overrides)
    return ClaudeAgentOptions(**params)


def message_text(message: Any) -> list[str]:
    if isinstance(message, AssistantMessage):
        return [block.text for block in message.content if isinstance(block, TextBlock)]
    return []


async def run_text(prompt: str, options: ClaudeAgentOptions) -> str:
    """Run a single-shot query and return the concatenated assistant text."""
    chunks: list[str] = []
    try:
        async for message in query(prompt=prompt, options=options):
            chunks.extend(message_text(message))
            if isinstance(message, ResultMessage) and message.result and not chunks:
                chunks.append(message.result)
    except CLINotFoundError as exc:
        raise RuntimeError(
            "The Claude Code CLI could not be located. It normally ships inside the "
            "claude-agent-sdk wheel; on unsupported platforms install it separately."
        ) from exc
    except ResultError as exc:
        raise RuntimeError(f"Claude Code run failed: {exc}") from exc
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def response_items_to_messages(items: Iterable[Any]) -> list[dict[str, str]]:
    """Translate Responses input/history items into simple role/content messages."""
    messages: list[dict[str, str]] = []
    for raw in items:
        item = raw if isinstance(raw, dict) else (raw.model_dump() if hasattr(raw, "model_dump") else {})
        if item.get("type") != "message":
            continue
        chunks: list[str] = []
        for part in item.get("content") or []:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict) and part.get("type") in {"input_text", "output_text", "text"}:
                chunks.append(str(part.get("text", "")))
        if chunks:
            messages.append({"role": str(item.get("role", "user")), "content": "\n".join(chunks)})
    return messages


async def request_messages(context: Any) -> list[dict[str, str]]:
    history = await context.get_history()
    current = await context.get_input_items()
    return response_items_to_messages(list(history) + list(current))


def messages_to_prompt(messages: list[dict[str, str]]) -> str:
    """Flatten a conversation into a single prompt.

    The CLI's streaming input channel only accepts user-role turns, so prior
    assistant turns are replayed as a labelled transcript rather than as real
    assistant messages.
    """
    if not messages:
        return ""
    if len(messages) == 1:
        return messages[0]["content"]
    lines = [f"{message['role']}: {message['content']}" for message in messages[:-1]]
    transcript = "\n".join(lines)
    latest = messages[-1]["content"]
    return f"Conversation so far:\n{transcript}\n\nCurrent request:\n{latest}"


async def prompt_from_context(context: Any) -> str:
    return messages_to_prompt(await request_messages(context))
