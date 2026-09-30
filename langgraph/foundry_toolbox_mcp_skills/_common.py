from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

load_dotenv()


def require_env(*names: str) -> list[str]:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
    return [os.environ[name] for name in names]


def build_model(**kwargs):
    endpoint, deployment = require_env(
        "FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME"
    )
    return AzureAIOpenAIApiChatModel(
        project_endpoint=endpoint,
        credential=DefaultAzureCredential(),
        model=deployment,
        use_responses_api=True,
        **kwargs,
    )


def port() -> int:
    return int(os.environ.get("PORT", "8088"))
