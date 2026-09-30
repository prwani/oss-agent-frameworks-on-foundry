import asyncio
import os
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MemorySearchOptions
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from common import kickoff_single,request_messages,require_env
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv()
app=ResponsesAgentServerHost()

# Lazy-initialize client to avoid blocking on startup
_project_client = None
_config = None

def get_project_client():
    global _project_client
    if _project_client is None:
        _project_client = AIProjectClient(
            endpoint=_config["FOUNDRY_PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(),
            allow_preview=True
        )
    return _project_client

def memory_turn(messages, user):
    global _config
    if _config is None:
        _config = require_env("FOUNDRY_PROJECT_ENDPOINT","MEMORY_STORE_NAME")

    current = messages[-1]["content"] if messages else ""
    project = get_project_client()

    # Memory search - errors propagate (no catch)
    found = project.beta.memory_stores.search_memories(
        name=_config["MEMORY_STORE_NAME"],
        scope=user,
        items=[{"type":"message","role":"user","content":current}],
        options=MemorySearchOptions(max_memories=5)
    )
    memories = "\n".join(str(m.memory_item.content) for m in found.memories)

    answer = kickoff_single(
        messages,
        role="Memory assistant",
        goal="Use relevant user memories without inventing facts",
        backstory="A privacy-conscious CrewAI assistant.",
        context="RELEVANT MEMORIES:\n"+memories
    )

    # Memory update - errors propagate (no catch)
    project.beta.memory_stores.begin_update_memories(
        name=_config["MEMORY_STORE_NAME"],
        scope=user,
        items=[
            {"type":"message","role":"user","content":current},
            {"type":"message","role":"assistant","content":answer},
        ],
        update_delay=0
    ).result()

    return answer

@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event):
    user = context.platform_context.user_id_key
    if not user:
        user = os.getenv("LOCAL_TEST_USER_ID")
    if not user:
        raise RuntimeError(
            "A platform user ID is required; set LOCAL_TEST_USER_ID only for local testing."
        )

    return TextResponse(context,request,text=await asyncio.to_thread(memory_turn,await request_messages(context),user))

if __name__=="__main__":
    app.run()
