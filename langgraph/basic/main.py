from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port

def main() -> None:
    graph = create_agent(
        build_model(),
        tools=[],
        system_prompt="You are a friendly assistant. Keep answers brief.",
    )
    ResponsesHostServer(graph).run(port=port())

if __name__ == "__main__":
    main()
