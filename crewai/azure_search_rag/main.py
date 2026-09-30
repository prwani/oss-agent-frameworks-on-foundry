import asyncio
import os
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from common import kickoff_single,request_messages,require_env
load_dotenv(); app=ResponsesAgentServerHost()
def search(q):
 c=require_env("AZURE_SEARCH_ENDPOINT","AZURE_SEARCH_INDEX_NAME")
 fields=[field.strip() for field in os.getenv("AZURE_SEARCH_SELECT","content,sourceName,sourceLink").split(",") if field.strip()]
 with SearchClient(c["AZURE_SEARCH_ENDPOINT"],c["AZURE_SEARCH_INDEX_NAME"],DefaultAzureCredential()) as client:
  return [{field: hit.get(field) for field in fields} for hit in client.search(q,top=3,select=fields)]
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
 messages=await request_messages(context); q=messages[-1]["content"] if messages else ""; hits=await asyncio.to_thread(search,q)
 evidence="\n\n".join(str(hit) for hit in hits)
 text=await asyncio.to_thread(kickoff_single,messages,role="RAG support specialist",goal="Answer only from retrieved evidence and cite source names",backstory="A grounded Contoso support agent.",context="RETRIEVED EVIDENCE:\n"+evidence); return TextResponse(context,request,text=text)
if __name__=="__main__": app.run()
