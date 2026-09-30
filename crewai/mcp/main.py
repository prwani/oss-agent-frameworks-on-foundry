import asyncio, os
from azure.ai.agentserver.responses import CreateResponse, ResponseContext, ResponsesAgentServerHost, TextResponse
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from common import kickoff_single, request_messages, require_env
load_dotenv(); app=ResponsesAgentServerHost()
def run(messages, endpoint, headers):
    with MCPServerAdapter({"url":endpoint,"transport":"streamable-http","headers":headers}) as tools:
        return kickoff_single(messages,role="MCP operator",goal="Use available MCP tools to answer",backstory="A CrewAI agent connected to a remote MCP server.",tools=list(tools))
@app.response_handler
async def handler(request: CreateResponse, context: ResponseContext, cancellation_signal: asyncio.Event):
    messages=await request_messages(context)
    endpoint=require_env("MCP_SERVER_URL")["MCP_SERVER_URL"]
    headers={"Authorization":"Bearer "+os.environ["MCP_AUTH_TOKEN"]} if os.getenv("MCP_AUTH_TOKEN") else {}
    return TextResponse(context,request,text=await asyncio.to_thread(run,messages,endpoint,headers))
if __name__=="__main__": app.run()
