# OSS Agent Frameworks on Microsoft Foundry

Equivalent Responses API hosted-agent samples for:

- [`langchain/`](langchain/)
- [`langgraph/`](langgraph/)
- [`crewai/`](crewai/)
- [`claude/`](claude/) (Claude Agent SDK)

## Sample matrix

| Agent scenario | Microsoft Agent Framework | LangChain | LangGraph | CrewAI | Claude Agent SDK |
|---|:---:|:---:|:---:|:---:|:---:|
| Basic Responses | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tools | ✅ | ✅ | ✅ | ✅ | ✅ |
| MCP | ✅ | ✅ | ✅ | ✅ | ✅ |
| Foundry Toolbox | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workflows | ✅ | ✅ | ✅ | ✅ | ✅ |
| Files | ✅ | ✅ | ✅ | ✅ | ✅ |
| Observability | ✅ | ✅ | ✅ | ✅ | ✅ |
| Azure AI Search RAG | ✅ | ✅ | ✅ | ✅ | ✅ |
| Foundry Memory | ✅ | ✅ | ✅ | ✅ | ✅ |
| Monty CodeAct | ✅ | ✅ | ✅ | ✅ | ✅ |
| Foundry Toolbox MCP Skills | ✅ | ✅ | ✅ | ✅ | ✅ |
| Resilient Long-Running Workflow | ✅ | ✅ | ✅ | ✅ | ✅ |
| Steerable Long-Running Agent | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom Storage | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ means that the repository contains an implementation of the scenario.
It does not imply full feature parity or a successful result for every runtime
path. See [`TEST_RESULTS.md`](TEST_RESULTS.md) for validated behavior and known
limitations.

The Claude Agent SDK column is **built but not yet validated against a live
Claude deployment**, and it differs from the other columns in an important way:
it can only run Anthropic Claude models, so it requires its own Claude
deployment in Foundry rather than the shared model deployment. See
[`claude/README.md`](claude/README.md) and
[`claude/support-matrix.yaml`](claude/support-matrix.yaml) for details.

The upstream Microsoft Agent Framework repository is retained as the
[`ms-agent-framework/`](ms-agent-framework/) Git submodule. Clone this
repository with submodules:

```bash
git clone --recurse-submodules <repository-url>
```

To advance the submodule to the latest upstream `main` commit:

```bash
git submodule update --remote ms-agent-framework
```

See
[`TEST_RESULTS.md`](TEST_RESULTS.md) for the local/hosted capability matrix,
exact limitations, evaluation result, and cost checkpoint.

## Environment

Copy [`.env.example`](.env.example) to `.env.local`, provide your own Azure
resource values, and load it into the shell before running deployment commands:

```bash
set -a
. ./.env.local
set +a
```

`.env.local` is ignored and must remain local. Do not commit project endpoints,
resource names, tenant/subscription identifiers, user identifiers, or
credentials.

The root `.venv` contains the LangChain/LangGraph and Microsoft Agent Framework
dependencies. `crewai/.venv` is intentionally separate because CrewAI requires
an incompatible OpenAI dependency range. Both environments use Python 3.13;
their frozen dependency snapshots are `local-requirements.lock` and
`crewai/local-requirements.lock`.

## Deployment

`azure.yaml` defines 42 direct-code hosted services: 14 capabilities for each
OSS framework. The project uses Responses protocol `2.0.0` and Python 3.13.

Every `azd` command for this project must set the Foundry user agent inline:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd deploy <service> --no-prompt
```

Resource-backed samples expect the pre-provisioned model, Search index, Memory
store, Toolbox, and skills documented in the per-sample READMEs. Their names
and endpoints are supplied through environment variables rather than committed
configuration. Public access or local authentication must not be enabled to
work around organization policy.
