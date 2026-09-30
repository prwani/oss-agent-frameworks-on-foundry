# Custom Storage

Custom SQLite conversation-chain dictionary storage with a Foundry-managed
hosted alternative.

## Run locally

Copy `.env.example` to `.env`, fill every placeholder, install `requirements.txt`, then run `python main.py`.
The service listens on `POST /responses` (default port 8088):

```bash
curl -N http://127.0.0.1:8088/responses -H 'content-type: application/json' \
  -d '{"input":"Hello","stream":true}'
```

## Deploy

`agent.yaml` declares a direct-code-compatible hosted agent using Responses protocol `2.0.0`.
Set `USE_FOUNDRY_STORAGE=true` for hosted deployment. The Responses host then
uses Foundry-managed conversation state, avoiding ephemeral container-local
SQLite. Leave it false and configure `SQLITE_STORAGE_PATH` for local testing.

## Notes

Custom SQLite conversation-chain dictionary storage. Missing required configuration raises an explicit startup error.

SQLite demonstrates the host's native conversation-chain store protocol.
Foundry-managed state is policy-compatible but is not a custom provider, so it
is classified as an alternative rather than exact parity.
