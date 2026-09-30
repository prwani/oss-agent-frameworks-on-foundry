# LangChain Microsoft Foundry Hosted Agents - Responses 2.0

Runnable LangChain equivalents for the Microsoft Agent Framework Responses
hosted-agent samples. Every hosted agent uses a compiled LangGraph, normally
produced by `langchain.agents.create_agent`, and the official
`langchain_azure_ai.agents.hosting.ResponsesHostServer`.

## Run a sample

Python 3.11 or newer is required; Python 3.13 matches the Foundry hosted-agent
runtime and is recommended.

```bash
cd basic
cp .env.example .env
# set FOUNDRY_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME
pip install -r requirements.txt
python main.py
curl -N http://127.0.0.1:8088/responses -H 'content-type: application/json'       -d '{"input":"Hello","stream":true}'
```

`agent.yaml` in every directory declares direct-code hosted configuration and
Responses protocol `2.0.0`. Resource-dependent examples intentionally raise on
absent configuration. They never create or silently substitute resources.

## Notes

- `FOUNDRY_PROJECT_ENDPOINT` must be a project endpoint, not an Azure OpenAI endpoint.
- `DefaultAzureCredential` includes Azure CLI credentials for local development.
- Preview platform behavior is called out in `support-matrix.yaml`.
- The host currently converts text Responses input. The files sample therefore
  exposes container files through constrained tools rather than `input_file`.
