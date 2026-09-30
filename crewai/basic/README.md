# CrewAI Basic — Foundry Responses 2.0

A minimal conversational CrewAI agent with multi-turn Responses history.

This service runs real CrewAI `Agent`/`Crew` logic and is exposed by Microsoft's framework-neutral `azure-ai-agentserver-responses` adapter. The handler translates Responses input and history items into CrewAI conversation messages and returns the Crew result as a Responses message item through `TextResponse`.

## Configure and run

Copy `.env.example` to `.env`, fill every required value, install `requirements.txt`, then run `python main.py`. Readiness is `GET /readiness`; invoke with `POST /responses` on port 8088.

Required: `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`. Authentication uses `DefaultAzureCredential` (Azure CLI locally, managed identity when hosted); no resource identifiers or secrets are embedded.

`agent.yaml` and `agent.manifest.yaml` declare the direct-code hosted-agent Responses protocol at version `2.0.0`.

## Adapter notes

CrewAI does not currently have a verified framework-specific Foundry Hosted Agent host. This sample therefore uses the official protocol adapter. CrewAI executes synchronously in a worker thread; protocol streaming is emitted by the adapter after CrewAI produces its result.

For capabilities that require duplex invocation, richer approval UX, or platform session mounts not exposed by Responses 2.0, use an Invocations-protocol host or Azure Container Apps and document the client contract explicitly.
