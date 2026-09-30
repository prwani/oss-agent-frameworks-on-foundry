import asyncio,base64,os
from pathlib import Path
import httpx
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from dotenv import load_dotenv
from common import kickoff_single,request_messages
load_dotenv(); app=ResponsesAgentServerHost(); MAX=2_000_000
def read_files(items):
 out=[]
 for raw in items:
  item=raw if isinstance(raw,dict) else raw.model_dump()
  for part in item.get("content") or []:
   if not isinstance(part,dict) or part.get("type")!="input_file": continue
   if part.get("file_data"): raw_bytes=base64.b64decode(part["file_data"].split(",",1)[1])
   elif part.get("file_url"):
    r=httpx.get(part["file_url"],follow_redirects=True,timeout=15); r.raise_for_status(); raw_bytes=r.content
   elif part.get("file_id"):
    root=os.getenv("AGENT_FILES_ROOT")
    if not root: raise RuntimeError("file_id requires AGENT_FILES_ROOT/session mounting; otherwise use file_data or file_url")
    base=Path(root).resolve(); path=(base/part["file_id"].lstrip("/")).resolve()
    if not path.is_relative_to(base): raise RuntimeError("file_id escapes AGENT_FILES_ROOT")
    raw_bytes=path.read_bytes()
   else: continue
   if len(raw_bytes)>MAX: raise RuntimeError("Input file exceeds the 2 MB sample limit")
   out.append(raw_bytes.decode("utf-8",errors="replace"))
 return out
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
 items=await context.get_input_items(); messages=await request_messages(context); docs=await asyncio.to_thread(read_files,items)
 text=await asyncio.to_thread(kickoff_single,messages,role="File analyst",goal="Answer from supplied files",backstory="A careful CrewAI document analyst.",context="FILES:\n"+"\n---\n".join(docs)); return TextResponse(context,request,text=text)
if __name__=="__main__": app.run()
