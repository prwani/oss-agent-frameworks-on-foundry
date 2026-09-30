# foundry_memory

Preview Foundry semantic memory middleware and retriever tool.

**Support:** `native`. Uses the native LangGraph `ResponsesHostServer` path.

## Run locally

Copy `.env.example` to `.env`, fill every placeholder, install `requirements.txt`, then run `python main.py`.
The service listens on `POST /responses` (default port 8088):

```bash
curl -N http://127.0.0.1:8088/responses -H 'content-type: application/json' \
  -d '{"input":"Hello","stream":true}'
```

## Deploy

`agent.yaml` declares a direct-code-compatible hosted agent using Responses protocol `2.0.0`.
Provision all named resources before deployment; this sample never creates resources.

## Notes

Preview Foundry semantic memory middleware and retriever tool. Missing required configuration raises an explicit startup error.

The Foundry Memory API and LangChain middleware are preview APIs; create the memory store separately.
The sample normalizes memory items to Responses `type: message` payloads and
waits for updates so persistence failures are visible.

For Entra-only Foundry resources, assign **Foundry User** at the account scope
to both the project managed identity and each hosted agent version identity.
Validation showed intermittent preview-service authentication failures against
the embedding deployment when `disableLocalAuth=true`.
