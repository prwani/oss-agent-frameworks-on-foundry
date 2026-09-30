# CrewAI Custom Storage — Foundry Responses 2.0

Persists CrewAI turns in Cosmos DB or SQLite, with Foundry-managed conversation
history as the hosted policy-compatible alternative.

This service runs real CrewAI `Agent`/`Crew` logic behind Microsoft's framework-neutral `azure-ai-agentserver-responses` adapter. Responses input and history items are translated to CrewAI messages; output is emitted as real Responses items through `TextResponse` or `ResponseEventStream`.

## Run
Copy `.env.example` to `.env`, fill required values, install `requirements.txt`, and run `python main.py`. Use `GET /readiness` and `POST /responses` on port 8088.

Required: `FOUNDRY_PROJECT_ENDPOINT` and
`AZURE_AI_MODEL_DEPLOYMENT_NAME`. Set `USE_FOUNDRY_STORAGE=true` for hosted
deployment, `USE_SQLITE_STORAGE=true` for local testing, or leave both false
and configure the Cosmos settings. Authentication uses
`DefaultAzureCredential`; no secrets or resource names are hardcoded.

## Adapter limitation
The Foundry-managed path uses the adapter's official Responses history and is
an alternative, not parity with a custom storage provider. The Cosmos path
remains available where network policy permits hosted-agent access.

Use an Invocations-protocol host or Azure Container Apps when a feature needs duplex interaction or a platform capability not exposed to a Responses handler.
