import asyncio
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port, require_env

async def load_tools():
    url, token = require_env("MCP_SERVER_URL", "MCP_AUTH_TOKEN")
    client = MultiServerMCPClient({"remote": {
        "transport": "http", "url": url,
        "headers": {"Authorization": f"Bearer {token}"},
    }})
    tools = await client.get_tools()
    if not tools:
        raise RuntimeError("The configured MCP server returned no tools")
    return tools

def main() -> None:
    tools = asyncio.run(load_tools())
    graph = create_agent(build_model(), tools=tools)
    ResponsesHostServer(graph).run(port=port())

if __name__ == "__main__":
    main()
