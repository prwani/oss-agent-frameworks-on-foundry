import asyncio
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.tools import AzureAIProjectToolbox
from _common import build_model, port, require_env

async def load_tools():
    toolbox_name = require_env("TOOLBOX_NAME")[0]
    tools = await AzureAIProjectToolbox(toolbox_name=toolbox_name).get_tools()
    if not tools:
        raise RuntimeError(f"Toolbox {toolbox_name!r} returned no tools")
    return tools

def main() -> None:
    graph = create_agent(build_model(), tools=asyncio.run(load_tools()))
    ResponsesHostServer(graph).run(port=port())

if __name__ == "__main__":
    main()
