# Foundry Memory

Foundry Memory Store middleware.

Fidelity: **preview**. `MEMORY_SCOPE` is mandatory and should identify one
tenant/user boundary; LangChain's middleware cannot currently substitute the
host's per-request user ID into the scope. Copy `.env.example` to `.env`, fill every resource
setting, install `requirements.txt`, then run `python main.py`. The service
listens on `PORT` (8088 by default) and exposes `POST /responses` using
Responses protocol `2.0.0`. Azure authentication uses `DefaultAzureCredential`;
locally, `az login` supplies `AzureCliCredential` through that chain.

Resource configuration is validated at startup. No sample provisions Azure
resources. See the root support matrix for limitations and alternatives.

The sample normalizes memory items to Responses `type: message` payloads and
waits for updates so persistence failures are visible. For Entra-only
resources, both the project managed identity and every hosted agent version
identity need **Foundry User** at the Foundry account scope. Validation showed
intermittent preview-service authentication failures against the embedding
deployment when `disableLocalAuth=true`.
