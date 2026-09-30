# Claude Agent SDK — Remote MCP server

Connects Claude to a remote MCP server declared directly in `ClaudeAgentOptions.mcp_servers`.

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
| `MCP_SERVER_URL` | yes |
| `MCP_AUTH_TOKEN` | yes |

Authentication uses `DefaultAzureCredential` against the `https://cognitiveservices.azure.com/.default` scope unless `ANTHROPIC_FOUNDRY_API_KEY` is set.
