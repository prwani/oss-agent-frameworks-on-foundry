"""Invoke a deployed hosted agent through the Azure AI Projects Responses client."""
import os
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def main() -> None:
    agent_name = required("FOUNDRY_AGENT_NAME")
    with (
        AzureCliCredential() as credential,
        AIProjectClient(
            endpoint=required("FOUNDRY_PROJECT_ENDPOINT"),
            credential=credential,
        ) as project,
        project.get_openai_client(agent_name=agent_name) as client,
    ):
        previous_response_id = None
        for prompt in ("Hi!", "Your name is Jarvis.", "What is your name?"):
            kwargs = {"input": prompt}
            if previous_response_id:
                kwargs["previous_response_id"] = previous_response_id
            response = client.responses.create(**kwargs)
            print(f"User: {prompt}\nAgent: {response.output_text}")
            previous_response_id = response.id

if __name__ == "__main__":
    main()
