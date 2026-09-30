import asyncio
from azure.ai.agentserver.responses import CreateResponse,ResponseContext,ResponsesAgentServerHost,TextResponse
from crewai import Agent,Crew,Process,Task
from dotenv import load_dotenv
from common import create_llm,request_messages
load_dotenv(); app=ResponsesAgentServerHost()
def run(messages):
 llm=create_llm(); transcript="\n".join(f"{m['role']}: {m['content']}" for m in messages)
 writer=Agent(role="Slogan writer",goal="Create a memorable slogan",backstory="Creative brand writer",llm=llm)
 legal=Agent(role="Legal reviewer",goal="Remove unsupported or risky claims",backstory="Advertising compliance reviewer",llm=llm)
 formatter=Agent(role="Retro formatter",goal="Present the approved slogan in retro terminal style",backstory="Concise content designer",llm=llm)
 t1=Task(description=f"Write one slogan for the latest request in:\n{transcript}",expected_output="One slogan",agent=writer)
 t2=Task(description="Review and correct the preceding slogan for legal safety.",expected_output="Approved corrected slogan",agent=legal,context=[t1])
 t3=Task(description="Format the approved slogan in compact retro terminal style.",expected_output="Final formatted slogan",agent=formatter,context=[t2])
 out=Crew(agents=[writer,legal,formatter],tasks=[t1,t2,t3],process=Process.sequential).kickoff(); return str(getattr(out,"raw",out))
@app.response_handler
async def handler(request:CreateResponse,context:ResponseContext,cancellation_signal:asyncio.Event): return TextResponse(context,request,text=await asyncio.to_thread(run,await request_messages(context)))
if __name__=="__main__": app.run()
