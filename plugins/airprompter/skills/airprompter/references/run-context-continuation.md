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
- Start a fresh run when the stored run is complete, the request targets a
  different workflow, or the context version is unsupported.
- Never fabricate missing step outputs. If an output is absent, say the stored
  run did not persist it and ask whether to re-run that step.

## Ambiguity

If it is unclear whether to continue or start fresh, or which stored run the
user means, show short A/B/C options using the selection format in
`references/ambiguity-handling.md`.
