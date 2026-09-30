from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from _common import build_model, port

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    draft: str
    reviewed: str

model = build_model()
async def writer(state: State):
    r = await model.ainvoke([SystemMessage(content="Write one memorable slogan."), *state["messages"]])
    return {"draft": str(r.content), "messages": [r]}
async def legal(state: State):
    r = await model.ainvoke([SystemMessage(content="Review for misleading legal claims; rewrite if needed."), HumanMessage(content=state["draft"])])
    return {"reviewed": str(r.content), "messages": [r]}
async def formatter(state: State):
    r = await model.ainvoke([SystemMessage(content="Format this as concise retro terminal art."), HumanMessage(content=state["reviewed"])])
    return {"messages": [r]}

graph = StateGraph(State)
graph.add_node("writer", writer); graph.add_node("legal", legal); graph.add_node("formatter", formatter)
graph.add_edge(START, "writer"); graph.add_edge("writer", "legal"); graph.add_edge("legal", "formatter"); graph.add_edge("formatter", END)

if __name__ == "__main__":
    ResponsesHostServer(graph.compile()).run(port=port())
