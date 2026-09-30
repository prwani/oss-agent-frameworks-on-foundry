import asyncio
from azure.ai.agentserver.responses import CreateResponse, ResponseContext, ResponsesAgentServerHost, TextResponse
from dotenv import load_dotenv
from common import kickoff_single, request_messages

load_dotenv()
app=ResponsesAgentServerHost()

@app.response_handler
async def handler(request: CreateResponse, context: ResponseContext, cancellation_signal: asyncio.Event):
    messages=await request_messages(context)
    text=await asyncio.to_thread(kickoff_single, messages, role='Helpful assistant', goal='Answer accurately and briefly', backstory='A dependable CrewAI assistant running behind the Foundry Responses protocol.')
    return TextResponse(context, request, text=text)

if __name__ == "__main__": app.run()
