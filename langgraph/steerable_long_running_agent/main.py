from azure.ai.agentserver.responses import ResponsesServerOptions
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port

graph = create_agent(
    build_model(streaming=True),
    tools=[],
    system_prompt="Count down one integer per line with a unique short remark before each number. Obey newer steering turns immediately.",
)
if __name__ == "__main__":
    ResponsesHostServer(graph, options=ResponsesServerOptions(steerable_conversations=True)).run(port=port())
