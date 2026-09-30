# Claude Agent SDK on Microsoft Foundry

Implementations of the fourteen Responses-API capability samples using the
[Claude Agent SDK for Python](https://github.com/anthropics/claude-agent-sdk-python),
served over the Foundry Responses protocol (version `2.0.0`).

## How this column differs

The other framework columns are Python libraries that call a chat-completions or
Responses endpoint directly. The Claude Agent SDK is not: it is a thin wrapper
that spawns the **bundled Claude Code CLI** as a subprocess and drives it over
newline-delimited JSON. Three consequences shape every sample here.

**1. Claude models only.** Model routing is configured through environment
variables that Claude Code understands. Its Microsoft Foundry backend
(`CLAUDE_CODE_USE_FOUNDRY`) targets Anthropic Claude models deployed in Foundry.
There is no supported way to point the SDK at a GPT deployment, so this column
needs its own Claude deployment rather than reusing the shared one.

**2. A different endpoint and token scope.** Claude models in Foundry are served
from the account-level Anthropic data plane:

| | Other columns | This column |
| --- | --- | --- |
| Endpoint | `https://<account>.services.ai.azure.com/api/projects/<project>` | `https://<resource>.services.ai.azure.com/anthropic/v1` |
| Entra scope | `https://ai.azure.com/.default` | `https://cognitiveservices.azure.com/.default` |

**3. Larger containers.** The SDK wheel is platform-specific and bundles a
~230 MB CLI binary, and the subprocess needs a writable working directory. These
agents are declared with 1 vCPU / 2 GiB rather than the 0.25 vCPU / 0.5 GiB used
elsewhere, and `CLAUDE_AGENT_WORKSPACE` must point at writable storage.

Hosting itself is unaffected: every sample uses the same official
`azure-ai-agentserver-responses` adapter as the other columns.

## Configuration

```bash
cp .env.example .env   # then fill in the values
```

| Variable | Required | Purpose |
| --- | --- | --- |
| `ANTHROPIC_FOUNDRY_RESOURCE` | yes | Foundry resource name hosting the Claude deployment |
| `ANTHROPIC_FOUNDRY_BASE_URL` | optional | Full endpoint override; mutually exclusive with the above |
| `CLAUDE_MODEL_DEPLOYMENT_NAME` | yes | Name of the Claude deployment |
| `ANTHROPIC_FOUNDRY_API_KEY` | optional | Use a key instead of Entra credentials |
| `CLAUDE_AGENT_WORKSPACE` | optional | Writable working directory (default `/tmp/claude-agent-workspace`) |

Authentication defaults to `DefaultAzureCredential`. A fresh bearer token is
requested per request, so long-lived hosts never serve an expired token.

> `ANTHROPIC_FOUNDRY_RESOURCE` and `ANTHROPIC_FOUNDRY_BASE_URL` are mutually
> exclusive — Claude Code fails if both are set. Because the SDK merges its
> environment *over* the parent process environment, `_common.py` explicitly
> blanks whichever one is unused.

## Running a sample

```bash
cd basic
pip install -r requirements.txt
python main.py
```

Each directory is independently deployable and carries its own `requirements.txt`,
`agent.yaml`, and `.env.example`.

## Capability support

See [`support-matrix.yaml`](support-matrix.yaml) for the authoritative per-sample
breakdown. In summary:

| Support | Samples |
| --- | --- |
| native | `basic`, `tools`, `mcp`, `files`, `observability`, `resilient_long_running_workflow`, `steerable_long_running_agent` |
| adapter | `foundry_toolbox`, `workflows`, `azure_search_rag`, `foundry_memory`, `monty_codeact`, `foundry_toolbox_mcp_skills` |
| alternative | `custom_storage` |

Where a capability has no native equivalent, the adapter is an in-process MCP
server built with `create_sdk_mcp_server` — the SDK's intended extension point.

## Verification status

The samples are built and statically verified but **not yet validated against a
live Claude deployment**. Confirmed so far:

- All fourteen samples import and start cleanly against the real SDK (`0.2.162`)
  and the real `azure-ai-agentserver-responses` host.
- The bundled CLI (`2.1.285`) supports `CLAUDE_CODE_USE_FOUNDRY` and the
  `ANTHROPIC_FOUNDRY_*` variables.
- An end-to-end request reaches the Foundry Anthropic endpoint and fails only at
  the credential/DNS boundary, confirming the wiring is correct.

Live request/response validation is pending Claude deployment credentials.
