from __future__ import annotations

import asyncio
import inspect
import json
import os
from typing import Any, Callable

from azure.identity import DefaultAzureCredential
from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from openai import OpenAI
from pydantic import PrivateAttr

_TOKEN_SCOPE = "https://ai.azure.com/.default"


def require_env(*names: str) -> dict[str, str]:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing required configuration: " + ", ".join(missing))
    return {name: os.environ[name] for name in names}


def foundry_base_url(endpoint: str) -> str:
    return endpoint.rstrip("/") + "/openai/v1/"


class FoundryResponsesLLM(BaseLLM):
    """CrewAI LLM backed by the project-scoped Foundry Responses API."""

    llm_type: str = "foundry_responses"
    _credential: Any = PrivateAttr()
    _endpoint: str = PrivateAttr()

    def __init__(self, *, endpoint: str, credential: Any, model: str, **kwargs: Any) -> None:
        super().__init__(model=model, provider="openai", **kwargs)
        self._credential = credential
        self._endpoint = endpoint

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Callable[..., Any]] | None = None,
        from_task: Any = None,
        from_agent: Any = None,
        response_model: Any = None,
    ) -> str:
        del callbacks, from_task
        client = OpenAI(
            base_url=foundry_base_url(self._endpoint),
            api_key=self._credential.get_token(_TOKEN_SCOPE).token,
        )
        response_input: Any = _normalize_messages(messages)
        request: dict[str, Any] = {"model": self.model, "input": response_input}
        normalized_tools = _normalize_tools(tools or [])
        if normalized_tools:
            request["tools"] = normalized_tools
        if response_model is not None:
            request["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                }
            }
        if not available_functions and from_agent is not None:
            available_functions = {}
            for candidate in getattr(from_agent, "tools", []):
                name = getattr(candidate, "name", None)
                function = getattr(candidate, "func", None) or getattr(candidate, "run", None)
                if isinstance(name, str) and callable(function):
                    available_functions[name] = function
        for _ in range(8):
            response = client.responses.create(**request)
            calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
            if not calls:
                return response.output_text or ""
            if not available_functions:
                raise RuntimeError("The model requested a tool, but CrewAI supplied no callable functions.")
            response_input = list(response_input) + [item.model_dump() for item in response.output]
            for call in calls:
                fn = available_functions.get(call.name)
                if fn is None:
                    raise RuntimeError(f"The model requested unknown tool {call.name!r}.")
                args = json.loads(call.arguments or "{}")
                value = fn(**args)
                if inspect.isawaitable(value):
                    value = asyncio.run(value)
                response_input.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": value if isinstance(value, str) else json.dumps(value, default=str),
                })
            request["input"] = response_input
        raise RuntimeError("Tool-call limit exceeded.")

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 128000


def _normalize_messages(messages: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(messages, str):
        return [{"type": "message", "role": "user", "content": messages}]
    result=[]
    for message in messages:
        role=message.get("role", "user")
        content=message.get("content", "")
        if isinstance(content, list):
            text=[]
            for part in content:
                if isinstance(part, str): text.append(part)
                elif isinstance(part, dict): text.append(str(part.get("text") or part.get("content") or ""))
            content="\n".join(filter(None,text))
        result.append({"type": "message", "role": role, "content": str(content)})
    return result


def _normalize_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result=[]
    for tool in tools:
        if tool.get("type") == "function" and "function" in tool:
            fn=tool["function"]
            result.append({"type":"function","name":fn["name"],"description":fn.get("description",""),"parameters":fn.get("parameters",{})})
        elif "name" in tool:
            result.append({"type":"function","name":tool["name"],"description":tool.get("description",""),"parameters":tool.get("parameters") or tool.get("args_schema") or {"type":"object","properties":{}}})
    return result


def response_items_to_messages(items: list[Any]) -> list[dict[str, str]]:
    """Translate Responses input/history items into CrewAI/OpenAI messages."""
    messages=[]
    for raw in items:
        item = raw if isinstance(raw, dict) else (raw.model_dump() if hasattr(raw,"model_dump") else {})
        if item.get("type") != "message":
            continue
        chunks=[]
        for part in item.get("content") or []:
            if isinstance(part, str): chunks.append(part)
            elif isinstance(part, dict) and part.get("type") in {"input_text","output_text","text"}:
                chunks.append(str(part.get("text", "")))
        if chunks:
            messages.append({"role": str(item.get("role", "user")), "content": "\n".join(chunks)})
    return messages


async def request_messages(context: Any) -> list[dict[str, str]]:
    history = await context.get_history()
    current = await context.get_input_items()
    return response_items_to_messages(list(history) + list(current))


def create_llm() -> FoundryResponsesLLM:
    cfg=require_env("FOUNDRY_PROJECT_ENDPOINT","AZURE_AI_MODEL_DEPLOYMENT_NAME")
    return FoundryResponsesLLM(endpoint=cfg["FOUNDRY_PROJECT_ENDPOINT"], model=cfg["AZURE_AI_MODEL_DEPLOYMENT_NAME"], credential=DefaultAzureCredential())


def kickoff_single(messages: list[dict[str,str]], *, role: str, goal: str, backstory: str, tools: list[Any] | None=None, context: str="") -> str:
    agent=Agent(role=role, goal=goal, backstory=backstory, llm=create_llm(), tools=tools or [], verbose=False)
    transcript="\n".join(f"{m['role']}: {m['content']}" for m in messages)
    task=Task(description=f"Conversation history and current request:\n{transcript}\n{context}\nAnswer the latest user request.", expected_output="A useful answer grounded in the supplied conversation and tool results.", agent=agent)
    result=Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False).kickoff()
    return str(getattr(result,"raw",result))
