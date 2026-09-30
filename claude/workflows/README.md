# Claude Agent SDK — Multi-stage workflow

A writer/legal/formatter pipeline built from Claude Agent SDK subagents.

Support level: **adapter**

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

Authentication uses `DefaultAzureCredential` against the `https://cognitiveservices.azure.com/.default` scope unless `ANTHROPIC_FOUNDRY_API_KEY` is set.
