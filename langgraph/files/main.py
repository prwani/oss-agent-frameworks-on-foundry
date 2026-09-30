import os
from pathlib import Path
from typing import Annotated
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from _common import build_model, port, require_env

def root() -> Path:
    value = require_env("DATA_DIR")[0]
    path = Path(value).resolve()
    if not path.is_dir():
        raise RuntimeError(f"DATA_DIR is not a directory: {path}")
    return path
def safe(path: str) -> Path:
    candidate = (root() / path).resolve()
    candidate.relative_to(root())
    return candidate
@tool
def list_files(subpath: Annotated[str, "Directory relative to DATA_DIR"] = "") -> list[str]:
    """List files below DATA_DIR."""
    return [p.relative_to(root()).as_posix() for p in safe(subpath).iterdir()]
@tool
def read_text_file(path: Annotated[str, "Text file relative to DATA_DIR"]) -> str:
    """Read at most 64 KiB of a UTF-8 file below DATA_DIR."""
    return safe(path).read_bytes()[:65536].decode("utf-8", errors="replace")

if __name__ == "__main__":
    graph = create_agent(build_model(), tools=[list_files, read_text_file])
    ResponsesHostServer(graph).run(port=port())
