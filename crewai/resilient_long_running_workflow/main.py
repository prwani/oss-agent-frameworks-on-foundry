import asyncio
from azure.ai.agentserver.core.tasks import set_resilient_tasks_enabled
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponseEventStream,ResponsesAgentServerHost,ResponsesServerOptions
from dotenv import load_dotenv
from common import kickoff_single,request_messages
load_dotenv(); app=ResponsesAgentServerHost(options=ResponsesServerOptions(resilient_background=True)); set_resilient_tasks_enabled(True)
PHASES=[("analyze","Analyze the request and identify constraints."),("generate","Produce a complete draft."),("refine","Critique and polish the draft.")]
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
 if context.is_recovery and context.persisted_response is not None: stream=ResponseEventStream(response_id=context.response_id,response=context.persisted_response); start=len(stream.response.get("output") or [])
 else: stream=ResponseEventStream(response_id=context.response_id,request=request); start=0
 yield stream.emit_created()
 if context.shutdown.is_set(): await context.exit_for_recovery()
 if cancellation_signal.is_set(): return
 yield stream.emit_in_progress(); messages=await request_messages(context)
 for phase,instruction in PHASES[start:]:
  answer=await asyncio.to_thread(kickoff_single,messages,role=f"{phase.title()} specialist",goal=instruction,backstory="One stage of a resilient CrewAI workflow.")
  for event in stream.output_item_message(f"[{phase}] {answer}"):
   yield event
  if context.shutdown.is_set(): await context.exit_for_recovery()
  if cancellation_signal.is_set(): return
  yield stream.checkpoint()
 yield stream.emit_completed()
if __name__=="__main__": app.run()
