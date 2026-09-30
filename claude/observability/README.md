# Claude Agent SDK — Observability

Traces both the Python host and the Claude Code subprocess with OpenTelemetry.

Support level: **native**

## Run locally

```bash
cp .env.example .env   # then fill in the values
pip install -r requirements.txt
python main.py
```

## Configuration

| Variable | Required |
| --- | --- |
| `ANTHROPIC_FOUNDRY_RESOURCE` | yes |
| `CLAUDE_MODEL_DEPLOYMENT_NAME` | yes |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | yes |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | optional |

Authentication uses `DefaultAzureCredential` against the `https://cognitiveservices.azure.com/.default` scope unless `ANTHROPIC_FOUNDRY_API_KEY` is set.
