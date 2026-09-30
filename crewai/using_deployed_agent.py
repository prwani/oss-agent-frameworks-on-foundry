import os
from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


def main():
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    agent_name = os.environ["FOUNDRY_AGENT_NAME"]
    previous = None

    with (
        AzureCliCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as project,
        project.get_openai_client(agent_name=agent_name) as client,
    ):
        for prompt in ["Hi!", "Your name is Jarvis. What can you do?", "What is your name?"]:
            kwargs = {"input": prompt}
            if previous:
                kwargs["previous_response_id"] = previous
            response = client.responses.create(**kwargs)
            print(f"User: {prompt}\nAgent: {response.output_text}\n")
            previous = response.id


if __name__ == "__main__":
    main()
