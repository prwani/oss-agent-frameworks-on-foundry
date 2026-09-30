from typing import Annotated
import pydantic_monty
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port

@tool
def execute_code(code: Annotated[str, "A Python expression without imports or filesystem access"]) -> str:
    """Execute a bounded Python expression in the Monty sandbox."""
    limits = pydantic_monty.ResourceLimits(max_duration_secs=3.0, max_memory=4 * 1024 * 1024)
    with pydantic_monty.Monty() as pool:
        with pool.checkout(limits=limits) as session:
            return repr(session.feed_run(code))

if __name__ == "__main__":
    graph = create_agent(build_model(), tools=[execute_code], system_prompt="Use execute_code for computation and data transformations.")
    ResponsesHostServer(graph).run(port=port())
