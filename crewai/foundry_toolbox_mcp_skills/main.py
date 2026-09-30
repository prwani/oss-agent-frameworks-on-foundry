import asyncio, os
from azure.ai.agentserver.core import get_request_context
from azure.ai.agentserver.responses import CreateResponse, ResponseContext, ResponsesAgentServerHost, TextResponse
from azure.identity import DefaultAzureCredential
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from common import kickoff_single, request_messages, require_env
load_dotenv(); app=ResponsesAgentServerHost()
def run(messages,endpoint,headers):
    with MCPServerAdapter({"url":endpoint,"transport":"streamable-http","headers":headers}) as tools:
        return kickoff_single(messages,role="Skilled toolbox operator",goal="Use Foundry Toolbox tools when useful",backstory="A CrewAI agent connected to Microsoft Foundry Toolbox.",tools=list(tools))
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
    messages=await request_messages(context)
    skill_text=open("skills/support-style/SKILL.md").read()+"\n"+open("skills/escalation-policy/SKILL.md").read()
    messages.insert(0,{"role":"system","content":skill_text})
    endpoint=os.getenv("TOOLBOX_ENDPOINT") or require_env("FOUNDRY_PROJECT_ENDPOINT","TOOLBOX_NAME")["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")+"/toolboxes/"+os.environ["TOOLBOX_NAME"]+"/mcp?api-version=v1"
    headers={"Authorization":"Bearer "+DefaultAzureCredential().get_token("https://ai.azure.com/.default").token,**get_request_context().platform_headers()}
    return TextResponse(context,request,text=await asyncio.to_thread(run,messages,endpoint,headers))
if __name__=="__main__": app.run()
