import asyncio
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_azure_ai.tools import AzureAIProjectToolbox
from _common import build_model, port, require_env

# Defer toolbox initialization to avoid blocking at import time
_toolbox = None

def get_toolbox():
    global _toolbox
    if _toolbox is None:
        _toolbox = AzureAIProjectToolbox(toolbox_name=require_env("TOOLBOX_NAME")[0])
    return _toolbox

@tool
async def load_skill(uri: str) -> str:
    """Load one SEP-2640 skill resource, such as skill://name/SKILL.md."""
    toolbox = get_toolbox()
    blobs = toolbox.get_resources(uris=uri)
    if not blobs:
        raise RuntimeError(f"No toolbox skill resource found for {uri}")
    return "\n".join(blob.as_string() for blob in blobs)

async def setup():
    toolbox = get_toolbox()
    tools = await toolbox.get_tools()
    index = toolbox.get_resources(uris="skill://index.json")
    if not index:
        raise RuntimeError("Toolbox does not expose skill://index.json")
    prompt = "Available skills index:\n" + "\n".join(x.as_string() for x in index)
    return create_agent(build_model(), tools=tools + [load_skill], system_prompt=prompt)

async def main():
    graph = await setup()
    server = ResponsesHostServer(graph)
    await server.run_async(port=port())

if __name__ == "__main__":
    asyncio.run(main())
