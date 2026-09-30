from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_azure_ai.agents.hosting import ResponsesHostServer
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI

SCOPE = "https://ai.azure.com/.default"

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def build_model() -> ChatOpenAI:
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=required("FOUNDRY_PROJECT_ENDPOINT"), credential=credential)
    client = project.get_openai_client()
    return ChatOpenAI(
        model=required("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        base_url=str(client.base_url),
        api_key=get_bearer_token_provider(credential, SCOPE),
        streaming=True,
        use_responses_api=True,
        output_version="responses/v1",
    )

load_dotenv()

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def build_graph():
    model = build_model()
    async def writer(state: State):
        return {"messages": [await model.ainvoke([SystemMessage("Write one original slogan for the user's topic."), *state["messages"]])]}
    async def legal(state: State):
        return {"messages": [await model.ainvoke([SystemMessage("Review the preceding slogan for legal risk and correct it."), state["messages"][-1]])]}
    async def formatter(state: State):
        return {"messages": [await model.ainvoke([SystemMessage("Format the preceding approved slogan in a concise retro terminal style."), state["messages"][-1]])]}
    builder = StateGraph(State)
    builder.add_node("writer", writer)
    builder.add_node("legal_reviewer", legal)
    builder.add_node("formatter", formatter)
    builder.add_edge(START, "writer")
    builder.add_edge("writer", "legal_reviewer")
    builder.add_edge("legal_reviewer", "formatter")
    builder.add_edge("formatter", END)
    return builder.compile()

def main() -> None:
    ResponsesHostServer(build_graph()).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
