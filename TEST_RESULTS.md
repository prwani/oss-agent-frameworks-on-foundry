# Foundry Hosted Agent Validation Results

Validation environment:

- Chat model: `gpt-5.4-mini`
- Embedding model: `text-embedding-3-small`
- Runtime: Python 3.13, direct-code deployment, Responses protocol `2.0.0`
- OSS environments: root `.venv` for LangChain/LangGraph and
  `crewai/.venv` for CrewAI

Statuses distinguish exact behavior from working alternatives:

- **Pass**: tested behavior completed successfully.
- **Partial**: primary path works, but an important parity or reliability
  requirement was not demonstrated.
- **Fail**: the tested capability did not satisfy its contract.
- **Alternative**: a tested policy-compatible implementation works but is not
  the upstream implementation.

## OSS hosted matrix

All 42 OSS services in `azure.yaml` deployed successfully and became active.

| Capability | LangChain | LangGraph | CrewAI | Hosted evidence |
|---|---|---|---|---|
| Basic | Pass | Pass | Pass | Exact response smoke tests passed; all three deployed-agent clients passed three-turn name/project recall. |
| Tools | Pass | Pass | Partial | Weather tools passed. LangChain and LangGraph emitted approval requests and executed `echo APPROVAL-CANARY-4482` after approval. CrewAI executes callable tools but has no Responses approval bridge; its shell tool is operator-gated. |
| MCP | Pass | Pass | Pass | All returned `Azure/azure-rest-api-specs` through the public GitMCP alternative. |
| Foundry Toolbox | Pass | Pass | Pass | Code interpreter returned `83810205` for `12345 * 6789`. |
| Workflows | Pass | Pass | Pass | Each framework completed its multi-step generation/review flow. |
| Files | Pass | Pass | Pass | LangChain/LangGraph read packaged bounded resources. CrewAI read an attached `input_file` and returned `FILE-CANARY-2846`; a prompt without an attachment is not a valid CrewAI file test. |
| Observability | Partial | Partial | Partial | Hosted response paths passed, but Application Insights contained no correlated request, dependency, or trace rows during validation. |
| Azure AI Search RAG | Pass | Pass | Pass | Grounded answers returned the indexed 30-day return policy after Search RBAC propagation. |
| Foundry Memory | Partial | Partial | Pass | CrewAI passed fresh-session recall of `ORBIT-5837`. LangGraph recalled the value but intermittently failed the response while updating memory. LangChain search/update intermittently failed because the preview Memory orchestrator could not authenticate to the embedding deployment with `disableLocalAuth=true`. |
| Monty CodeAct | Pass | Pass | Pass | Each bounded sandbox returned `42` for `6 * 7`. |
| Toolbox MCP Skills | Alternative | Pass | Alternative | LangGraph loaded `skill://support-style/SKILL.md` from Toolbox after agent RBAC was added. LangChain and CrewAI use packaged skills because their native skill-provider lifecycle is unavailable. |
| Custom Storage | Alternative | Alternative | Alternative | All three deployed alternatives passed multi-turn recall of `VAULT-2718`/`Aurora` using Foundry-managed conversation state. SQLite remains the local fallback; Cosmos remains available where network policy permits it. |
| Resilient Workflow | Partial | Partial | Partial | Ordered staged countdowns completed, but these OSS samples were not proven to resume from a hard process crash. |
| Steerable Agent | Fail | Fail | Fail | LangChain/LangGraph completed the original countdown before the replacement. CrewAI completed the replacement but left the original response `in_progress`. This is not active-turn replacement. |

## Microsoft Agent Framework matrix

| Capability | Local | Hosted | Evidence or limitation |
|---|---|---|---|
| Basic | Pass | Pass | Exact output, `previous_response_id`, service-managed session, user-managed session, three-turn recall, and cleanup passed. |
| Tools | Pass | Partial | Weather passed. Approval request emission passed, but the approval continuation requested approval again instead of executing. |
| MCP | Pass | Alternative | Public GitMCP alternative passed without introducing a GitHub PAT. |
| Foundry Toolbox | Pass | Pass | Code interpreter returned `83810205`. |
| Workflows | Pass | Pass | Workflow output completed. |
| Files | Pass | Pass | A session file was found and read; the computed revenue difference was `$151.9M`. |
| Observability | Pass | Partial | Response path passed; no correlated Application Insights telemetry was found. |
| Azure AI Search RAG | Pass | Pass | Returned the grounded 30-day policy after assigning Search Index Data Reader. |
| Foundry Memory | Partial | Partial | Same-session recall worked, but fresh-session recall returned unrelated generated values; semantic persistence was not proven. |
| Monty CodeAct | Pass | Partial | Simple multiplication returned `42`; a more complex async program produced empty tool output. |
| Toolbox MCP Skills | Pass | Fail | Skill discovery and `load_skill` invocation occurred, but hosted tool execution returned `Error: Function failed`. |
| Custom Storage | Alternative | Blocked | Managed identity and Cosmos data RBAC were valid, but organization policy blocks hosted-agent VNet traffic at the Cosmos firewall. Public access was not weakened. |
| Resilient Workflow | Pass | Partial | A forced local process kill resumed from checkpoint without lost or duplicate steps. Hosted managed compute completed the workflow but did not expose a safe hard-kill test. |
| Steerable Agent | Fail | Fail | The original local turn completed and the second failed; hosted in-progress response/session resolution also failed. |

## Local OSS validation

- Python source compilation passes for all project files in `langchain/`,
  `langgraph/`, and `crewai/`.
- LangChain/LangGraph use the root Python 3.13 `.venv`; CrewAI uses its
  isolated Python 3.13 `crewai/.venv` because its OpenAI dependency constraint
  conflicts with the root Azure AI Projects stack.
- CrewAI local tool execution passed for weather, GitMCP, Foundry Toolbox code
  interpreter, and Monty after the adapter learned to map CrewAI `Tool`
  objects to callables.
- SQLite custom-storage fallbacks passed locally.
- Memory remains a preview external-service dependency; errors are propagated
  rather than replaced with model-only or invented memory.
- The only proven hard-crash recovery is the Microsoft Agent Framework
  workflow. Ordered countdown output alone is not counted as crash recovery.

## Evaluation and cost

The Microsoft Agent Framework Basic instruction-generated evaluation contained
15 cases: 12 passed, 3 failed, and 0 errored.

The shared resource group's month-to-date cost included pre-existing workloads
unrelated to this project, so the bill could not reliably isolate this
project's spend. Additional OSS evaluation suites were therefore not run
against the approved project cap.

## Known platform constraints

- Foundry Memory is preview. The project managed identity and each hosted
  agent version identity require **Foundry User** at the Foundry account scope.
  With `disableLocalAuth=true`, the Memory orchestrator intermittently returned
  embedding authentication failures even after correct RBAC; the sample does
  not weaken the account policy.
- The Cosmos account remains private and local authentication remains disabled.
  Foundry-managed conversation state is therefore the selected hosted
  custom-storage alternative.
- Hosted agents scale to zero, but deployed versions and shared dependencies
  remain provisioned until explicitly removed.
