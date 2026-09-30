# CrewAI + Microsoft Foundry Hosted Agents (Responses 2.0)

Each directory is independently deployable and includes CrewAI logic, the official `azure-ai-agentserver-responses` adapter, dependencies, environment template, README, and direct-code configuration.

## Samples

- [`basic/`](basic/README.md)
- [`tools/`](tools/README.md)
- [`mcp/`](mcp/README.md)
- [`foundry_toolbox/`](foundry_toolbox/README.md)
- [`workflows/`](workflows/README.md)
- [`files/`](files/README.md)
- [`observability/`](observability/README.md)
- [`azure_search_rag/`](azure_search_rag/README.md)
- [`foundry_memory/`](foundry_memory/README.md)
- [`monty_codeact/`](monty_codeact/README.md)
- [`foundry_toolbox_mcp_skills/`](foundry_toolbox_mcp_skills/README.md)
- [`custom_storage/`](custom_storage/README.md)
- [`resilient_long_running_workflow/`](resilient_long_running_workflow/README.md)
- [`steerable_long_running_agent/`](steerable_long_running_agent/README.md)
- [`using_deployed_agent.py`](using_deployed_agent.py)

Authentication uses `DefaultAzureCredential` in services and `AzureCliCredential` in the client. Resource samples require existing resources and never provision or deploy them. See `support-matrix.yaml` for fidelity notes.
