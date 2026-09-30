# LangGraph Foundry Hosted Agents — Responses v2

Current LangGraph equivalents of the Microsoft Agent Framework Responses samples. Every directory is independently runnable and direct-code deployable, uses `FOUNDRY_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and exposes `POST /responses` through `langchain-azure-ai[hosting]` `ResponsesHostServer`.

Python 3.11 or newer is required; Python 3.13 matches the Foundry hosted-agent runtime and is recommended.

## Samples

| Sample | Support | Capability |
|---|---|---|
| `basic` | native | Minimal hosted agent |
| `tools` | native | Typed tools and approval interrupts |
| `mcp` | native | Remote MCP |
| `foundry_toolbox` | native | Foundry Toolbox |
| `workflows` | native | Multi-node workflow |
| `files` | alternative | Container filesystem tools |
| `observability` | native | OpenTelemetry |
| `azure_search_rag` | adapter | Azure AI Search tool |
| `foundry_memory` | native/preview | Foundry semantic memory |
| `monty_codeact` | adapter | Monty sandbox |
| `foundry_toolbox_mcp_skills` | adapter/preview | Toolbox SEP-2640 skills |
| `custom_storage` | native | Conversation-chain store protocol |
| `resilient_long_running_workflow` | native | Durable background execution |
| `steerable_long_running_agent` | native | Active-turn steering |

Copy a sample's `.env.example` to `.env`, fill all placeholders, install its requirements, and run `python main.py`. No sample provisions or modifies Azure resources. See `support-matrix.yaml` for exact dependencies and limitations.

`using_deployed_agent.py` invokes an already-deployed hosted agent with the current `azure-ai-projects` OpenAI Responses client and an explicit hosted-agent session.
