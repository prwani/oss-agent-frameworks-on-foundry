# Observability

OpenTelemetry tracing to OTLP or Azure Monitor.

Fidelity: **exact**. Copy `.env.example` to `.env`, fill every resource
setting, install `requirements.txt`, then run `python main.py`. The service
listens on `PORT` (8088 by default) and exposes `POST /responses` using
Responses protocol `2.0.0`. Azure authentication uses `DefaultAzureCredential`;
locally, `az login` supplies `AzureCliCredential` through that chain.

Resource configuration is validated at startup. No sample provisions Azure
resources. See the root support matrix for limitations and alternatives.
