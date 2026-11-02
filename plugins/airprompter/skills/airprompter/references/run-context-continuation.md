# Run Context Continuation

Use this reference when an orchestrator host receives a shareable AirPrompter
run context and must decide how to carry a stored run's context forward.

## What The Run Context Is

- A read-only DTO shared at the customer's direction. It has no write or
  mutation surface; continuing work always goes through AirPrompter MCP tools.
- `contextVersion` gates the shape. Treat an unknown version as unsupported
  and say so instead of guessing at fields.
- It carries step titles, step statuses, and step outputs only. Outputs are
  present only when the actor's store-run-results consent persisted them.
- Prompt bodies are deliberately excluded. Never infer, reconstruct, or ask
  another agent to reproduce them.

## Continue Or Start Fresh

- Offer to continue the stored run when the context shows incomplete steps and
  the user's request targets the same workflow.
- A completed stored run cannot continue. Start fresh only when the user asks
  to run again or the new request requires a new run. If the context version is
  unsupported, stop interpretation; rediscover the workflow through MCP only
  when the user has requested a fresh execution.
- Never fabricate missing step outputs. If an output is absent, say the stored
  run did not persist it. A missing output is not permission to repeat an outside
  effect; verify its outcome or obtain explicit retry direction first.
- Retain the original connector/environment/account binding. A shared DTO is
  context, not authorization to transfer its run ID to another connection.
- Read authoritative state before continuation and dispatch using the server
  response as [workflow execution](workflow-execution.md) describes. Routed
  occurrences, versions, eligible targets, and finite budgets come from the
  routed get response, never from stored step ordering or inferred graphs.
- Reading context or run status does not authorize advancing or re-executing.
  Paused and failed runs follow their explicit stop rules; no silent resume.

## Ambiguity

If it is unclear whether to continue or start fresh, or which stored run the
user means, show short A/B/C options using the selection format in
[ambiguity handling](ambiguity-handling.md).
