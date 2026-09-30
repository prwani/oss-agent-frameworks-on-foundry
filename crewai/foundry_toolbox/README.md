# CrewAI Foundry Toolbox — Foundry Responses 2.0

Connects CrewAI to a Foundry Toolbox MCP endpoint and forwards the per-request Foundry call ID.

This service runs real CrewAI `Agent`/`Crew` logic behind Microsoft's framework-neutral `azure-ai-agentserver-responses` adapter. Responses input and history items are translated to CrewAI messages; output is emitted as real Responses items through `TextResponse` or `ResponseEventStream`.

## Run
Copy `.env.example` to `.env`, fill required values, install `requirements.txt`, and run `python main.py`. Use `GET /readiness` and `POST /responses` on port 8088.

Required: `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `TOOLBOX_ENDPOINT` or `TOOLBOX_NAME`. Authentication uses `DefaultAzureCredential`; no secrets or resource names are hardcoded. `agent.yaml` and `agent.manifest.yaml` declare direct-code Responses `2.0.0`.

## Adapter limitation
Toolbox approval and elicitation UX is not represented by CrewAI; configure unattended tools.

Use an Invocations-protocol host or Azure Container Apps when a feature needs duplex interaction or a platform capability not exposed to a Responses handler.
