import asyncio,json
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from crewai.tools import tool
from dotenv import load_dotenv
from pydantic_monty import Monty
from common import kickoff_single,request_messages
load_dotenv(); app=ResponsesAgentServerHost()
def compute(operation,a,b): return {"add":a+b,"subtract":a-b,"multiply":a*b,"divide":a/b}[operation]
def fetch_data(table): return {"users":[{"name":"Alice","role":"admin"},{"name":"Bob","role":"user"}],"products":[{"name":"Widget","price":9.99},{"name":"Gadget","price":19.99}]}.get(table,[])
@tool("execute_code")
def execute_code(code:str)->str:
 """Execute sandboxed Python with compute(operation,a,b) and fetch_data(table)."""
 with Monty() as pool:
  with pool.checkout() as session: return json.dumps(session.feed_run(code,external_lookup={"compute":compute,"fetch_data":fetch_data}),default=str)
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
 text=await asyncio.to_thread(kickoff_single,await request_messages(context),role="CodeAct analyst",goal="Use sandboxed Python for calculations and transformations",backstory="A CrewAI analyst with a pydantic-monty sandbox.",tools=[execute_code]); return TextResponse(context,request,text=text)
if __name__=="__main__": app.run()
