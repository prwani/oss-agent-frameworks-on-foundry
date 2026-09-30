import asyncio, os, random, subprocess
from azure.ai.agentserver.responses import CreateResponse, ResponseContext, ResponsesAgentServerHost, TextResponse
from crewai.tools import tool
from dotenv import load_dotenv
from common import kickoff_single, request_messages
load_dotenv(); app=ResponsesAgentServerHost()
@tool("get_weather")
def get_weather(location: str) -> str:
    """Return simulated weather for a location."""
    return f"{location}: {random.choice(['sunny','cloudy','rainy'])}, {random.randint(10,30)} C"
@tool("run_shell_command")
def run_shell_command(command: str) -> str:
    """Run a shell command only when the operator explicitly enabled unsafe shell access."""
    if os.getenv("ALLOW_UNSAFE_SHELL") != "true": return "Denied: set ALLOW_UNSAFE_SHELL=true to enable this high-risk demo tool."
    result=subprocess.run(command, shell=True, text=True, capture_output=True, timeout=30)
    return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\nexit_code:{result.returncode}"
@app.response_handler
async def handler(request: CreateResponse, context: ResponseContext, cancellation_signal: asyncio.Event):
    messages=await request_messages(context)
    text=await asyncio.to_thread(kickoff_single,messages,role="Tool-using assistant",goal="Use tools when needed and explain results",backstory="A cautious CrewAI operator.",tools=[get_weather,run_shell_command])
    return TextResponse(context,request,text=text)
if __name__=="__main__": app.run()
