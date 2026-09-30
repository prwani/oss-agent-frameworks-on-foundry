from pathlib import Path
from typing import Annotated
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import ChatOpenAI

SCOPE = "https://ai.azure.com/.default"

def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def build_model() -> ChatOpenAI:
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=required("FOUNDRY_PROJECT_ENDPOINT"), credential=credential)
    client = project.get_openai_client()
    return ChatOpenAI(
        model=required("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        base_url=str(client.base_url),
        api_key=get_bearer_token_provider(credential, SCOPE),
        streaming=True,
        use_responses_api=True,
        output_version="responses/v1",
    )

load_dotenv()
HERE = Path(__file__).resolve().parent

def root() -> Path:
    value = Path(os.getenv("DATA_DIR", str(HERE / "resources"))).resolve()
    if not value.is_dir():
        raise RuntimeError(f"DATA_DIR does not exist or is not a directory: {value}")
    return value

def safe(path: str) -> Path:
    candidate = (root() / path).resolve()
    try:
        candidate.relative_to(root())
    except ValueError as exc:
        raise ValueError("Path escapes DATA_DIR") from exc
    return candidate

@tool
def list_files(directory: Annotated[str, "Relative directory; use an empty string for root."] = "") -> list[str]:
    """List entries below the configured data directory."""
    return [p.relative_to(root()).as_posix() for p in safe(directory).iterdir()]

@tool
def read_file(file_path: Annotated[str, "Relative UTF-8 text file path."]) -> str:
    """Read at most 64 KiB from a text file below the data directory."""
    return safe(file_path).read_bytes()[:65536].decode("utf-8", errors="replace")

def main() -> None:
    root()
    graph = create_agent(build_model(), tools=[list_files, read_file],
                         system_prompt="Use file tools to inspect only the configured data directory.")
    ResponsesHostServer(graph).run(port=int(os.getenv("PORT", "8088")))

if __name__ == "__main__":
    main()
