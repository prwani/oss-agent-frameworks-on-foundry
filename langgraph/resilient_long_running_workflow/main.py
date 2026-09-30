import asyncio, os, re
from typing import Annotated, TypedDict
from azure.ai.agentserver.core import AgentConfig
from azure.ai.agentserver.responses import ResponsesServerOptions
from langchain_core.messages import BaseMessage, AIMessage
from langchain_azure_ai.agents.hosting import FoundryCheckpointSaver, ResponsesHostServer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from _common import build_model, port

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining: int
async def parse(state: State):
    text = str(state["messages"][-1].content)
    match = re.search(r"\b([1-9]\d*)\b", text)
    target = int(match.group(1)) if match else 5
    reply = await build_model().ainvoke(
        f"Acknowledge in one short sentence that a durable countdown from {target} is starting."
    )
    return {"remaining": target, "messages": [reply]}
async def tick(state: State):
    await asyncio.sleep(1)
    n = state["remaining"]
    return {"remaining": n - 1, "messages": [AIMessage(content=f"{n}")]}
def route(state: State): return "tick" if state["remaining"] > 0 else "end"
def graph(cp):
    g=StateGraph(State); g.add_node("parse",parse); g.add_node("tick",tick)
    g.add_edge(START,"parse"); g.add_conditional_edges("parse",route,{"tick":"tick","end":END})
    g.add_conditional_edges("tick",route,{"tick":"tick","end":END})
    return g.compile(checkpointer=cp)
async def main():
    ctx = FoundryCheckpointSaver(user_isolation=True) if AgentConfig.from_env().is_hosted else AsyncSqliteSaver.from_conn_string(os.environ.get("CHECKPOINT_DB","checkpoints.sqlite"))
    async with ctx as cp:
        await ResponsesHostServer(graph(cp), options=ResponsesServerOptions(resilient_background=True)).run_async(port=port())
if __name__ == "__main__": asyncio.run(main())
