# files

Sandboxed filesystem tools; request input_file passthrough is not yet native.

**Support:** `alternative`. Uses the closest deployable alternative; see the limitation below.

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

Sandboxed filesystem tools; request input_file passthrough is not yet native. Missing required configuration raises an explicit startup error.

Responses `input_file` conversion is not currently exposed by the LangGraph host, so mounted filesystem tools are the supported alternative.
