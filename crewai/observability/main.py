import asyncio
import logging
import os
from azure.ai.agentserver.responses import CreateResponse, ResponseContext, ResponsesAgentServerHost, TextResponse
from dotenv import load_dotenv
from common import kickoff_single, request_messages

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Initialize telemetry only if connection string is provided and valid
def configure_telemetry():
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn_str:
        log.info("Azure Monitor telemetry is not configured")
        return
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=conn_str)
    log.info("Azure Monitor telemetry enabled")

# Initialize telemetry lazily on first request
_telemetry_initialized = False

app = ResponsesAgentServerHost()

@app.response_handler
async def handler(request: CreateResponse, context: ResponseContext, cancellation_signal: asyncio.Event):
    global _telemetry_initialized
    if not _telemetry_initialized:
        configure_telemetry()
        _telemetry_initialized = True

    messages = await request_messages(context)
    text = await asyncio.to_thread(kickoff_single, messages, role='Observable assistant', goal='Answer accurately and briefly', backstory='A dependable CrewAI assistant running behind the Foundry Responses protocol.')
    return TextResponse(context, request, text=text)

if __name__ == "__main__":
    app.run()
