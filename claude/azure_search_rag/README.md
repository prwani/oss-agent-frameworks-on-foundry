# Claude Agent SDK — Azure AI Search RAG

Grounds answers in an existing Azure AI Search index via a retrieval MCP tool.

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
| `AZURE_SEARCH_ENDPOINT` | yes |
| `AZURE_SEARCH_INDEX_NAME` | yes |

Authentication uses `DefaultAzureCredential` against the `https://cognitiveservices.azure.com/.default` scope unless `ANTHROPIC_FOUNDRY_API_KEY` is set.
