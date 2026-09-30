# CrewAI Foundry Memory — Foundry Responses 2.0

Searches and updates a pre-provisioned Foundry Memory Store scoped to the authenticated user.

This service runs real CrewAI `Agent`/`Crew` logic behind Microsoft's framework-neutral `azure-ai-agentserver-responses` adapter. Responses input and history items are translated to CrewAI messages; output is emitted as real Responses items through `TextResponse` or `ResponseEventStream`.

## Run
Copy `.env.example` to `.env`, fill required values, install `requirements.txt`, and run `python main.py`. Use `GET /readiness` and `POST /responses` on port 8088.

Required: `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `MEMORY_STORE_NAME`. Authentication uses `DefaultAzureCredential`; no secrets or resource names are hardcoded. `agent.yaml` and `agent.manifest.yaml` declare direct-code Responses `2.0.0`.

## Adapter limitation
Memory Stores are preview. The store and chat/embedding deployments must already exist; this service never provisions resources.

Memory search and update items include the required Responses
`type: message` discriminator, and failures propagate to the caller. For
Entra-only resources, both the project managed identity and every hosted agent
version identity need **Foundry User** at the Foundry account scope. Validation
showed intermittent preview-service authentication failures against the
embedding deployment when `disableLocalAuth=true`.

Use an Invocations-protocol host or Azure Container Apps when a feature needs duplex interaction or a platform capability not exposed to a Responses handler.
