# workflows

Three-stage writer, legal review, and formatter LangGraph workflow.

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

Three-stage writer, legal review, and formatter LangGraph workflow. Missing required configuration raises an explicit startup error.
