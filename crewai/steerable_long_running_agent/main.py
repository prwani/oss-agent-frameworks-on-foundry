import asyncio
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponseEventStream,ResponsesAgentServerHost,ResponsesServerOptions
from dotenv import load_dotenv
from common import kickoff_single,request_messages
load_dotenv(); app=ResponsesAgentServerHost(options=ResponsesServerOptions(resilient_background=True,steerable_conversations=True))
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
 stream=ResponseEventStream(response_id=context.response_id,request=request); yield stream.emit_created()
 if context.shutdown.is_set(): await context.exit_for_recovery()
 if cancellation_signal.is_set():
  if context.pending_input_count: yield stream.emit_completed()
  return
 yield stream.emit_in_progress(); answer=await asyncio.to_thread(kickoff_single,await request_messages(context),role="Steerable assistant",goal="Follow the newest user direction",backstory="A CrewAI agent whose output may be superseded.")
 msg=stream.add_output_item_message(); yield msg.emit_added(); text=msg.add_text_content(); yield text.emit_added(); acc=""
 for token in answer.split():
  if cancellation_signal.is_set() or context.shutdown.is_set(): break
  piece=token+" "; acc+=piece; yield text.emit_delta(piece); await asyncio.sleep(0.03)
 yield text.emit_text_done(acc.strip()); yield text.emit_done(); yield msg.emit_done()
 if context.shutdown.is_set(): await context.exit_for_recovery()
 yield stream.emit_completed()
if __name__=="__main__": app.run()
