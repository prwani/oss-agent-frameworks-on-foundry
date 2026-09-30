# Custom Storage

This sample supports three explicit backends: Cosmos DB checkpoints, a local
SQLite conversation-chain store, and Foundry-managed conversation state.

For local testing, set `USE_SQLITE_STORAGE=true`. For hosted deployment, set
`USE_FOUNDRY_STORAGE=true`; this is the policy-compatible alternative when the
Cosmos account does not permit traffic from the hosted-agent network. Set both
flags to `false` to use Cosmos DB with `DefaultAzureCredential`.

The Foundry-managed path preserves Responses conversation history, but it is an
alternative rather than parity with Agent Framework's custom
`SessionStoreProvider`.
