from __future__ import annotations

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import VersionRefIndicator
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    endpoint = required("FOUNDRY_PROJECT_ENDPOINT")
    agent_name = required("FOUNDRY_AGENT_NAME")
    requested_version = os.environ.get("FOUNDRY_AGENT_VERSION")

    with (
        AzureCliCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project,
        project.get_openai_client(agent_name=agent_name) as responses,
    ):
        if requested_version:
            version = requested_version
        else:
            agent = project.agents.get(agent_name=agent_name)
            version = agent.versions.latest.version

        session = project.agents.create_session(
            agent_name=agent_name,
            version_indicator=VersionRefIndicator(agent_version=version),
        )
        try:
            previous_response_id = None
            for prompt in ("Hello!", "Remember that my project is called Aurora.", "What is my project called?"):
                kwargs = {
                    "input": prompt,
                    "extra_body": {"agent_session_id": session.agent_session_id},
                }
                if previous_response_id:
                    kwargs["previous_response_id"] = previous_response_id
                response = responses.responses.create(**kwargs)
                print(f"User: {prompt}\nAgent: {response.output_text}\n")
                previous_response_id = response.id
        finally:
            project.agents.delete_session(
                agent_name=agent_name,
                session_id=session.agent_session_id,
            )


if __name__ == "__main__":
    main()
