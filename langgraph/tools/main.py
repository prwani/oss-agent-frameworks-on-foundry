from __future__ import annotations
import subprocess
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from azure.ai.agentserver.core import AgentConfig
from langchain_azure_ai.agents.hosting import FoundryCheckpointSaver, ResponsesHostServer
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from _common import build_model, port

@tool
def get_weather(location: Annotated[str, "City and country"]) -> str:
    """Return deterministic demonstration weather."""
    return f"The demonstration forecast for {location} is sunny, 21C."

@tool
def run_command(command: Annotated[str, "One of: pwd, date, or echo TEXT"]) -> str:
    """Run an allow-listed local command after explicit approval."""
    parts = command.split()
    if not parts or parts[0] not in {"pwd", "date", "echo"}:
        raise ValueError("Only pwd, date, and echo are allowed")
    result = subprocess.run(parts, capture_output=True, text=True, timeout=10, check=False)
    return (result.stdout + result.stderr).strip() or f"exit_code={result.returncode}"

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

TOOLS = [get_weather, run_command]

def build_graph():
    model = build_model().bind_tools(TOOLS)
    by_name = {tool.name: tool for tool in TOOLS}
    async def agent(state: State):
        reply = await model.ainvoke([
            SystemMessage(content="Use tools when useful. Commands require user approval."),
            *state["messages"],
        ])
        return {"messages": [reply]}
    async def approved_tools(state: State):
        message = state["messages"][-1]
        assert isinstance(message, AIMessage)
        outputs = []
        for call in message.tool_calls:
            if call["name"] == "run_command":
                approved = interrupt({"prompt": "Approve local command?", "tool_call": call})
                if not approved:
                    outputs.append(ToolMessage(content="Rejected by user.", tool_call_id=call["id"]))
                    continue
            value = await by_name[call["name"]].ainvoke(call["args"])
            outputs.append(ToolMessage(content=str(value), tool_call_id=call["id"]))
        return {"messages": outputs}
    def route(state: State):
        last = state["messages"][-1]
        return "tools" if isinstance(last, AIMessage) and last.tool_calls else "end"
    graph = StateGraph(State)
    graph.add_node("agent", agent)
    graph.add_node("tools", approved_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph

async def main():
    checkpointer = (
        FoundryCheckpointSaver(user_isolation=True)
        if AgentConfig.from_env().is_hosted
        else InMemorySaver()
    )
    async with checkpointer:
        graph = build_graph().compile(checkpointer=checkpointer)
        await ResponsesHostServer(graph).run_async(port=port())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
