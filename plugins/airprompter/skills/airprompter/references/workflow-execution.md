# Workflow Execution

Use this reference when the user asks to run, execute, use, continue, or apply a
saved AirPrompter workflow, Airflow, prompt, or prompt chain.

## Required Behavior

- Use AirPrompter MCP before using native model, image, file, or search tools.
- If the user gives a workflow id, start from that id.
- If the user gives a title or description, discover or resolve matching
  workflows first. Do not ask for an id before trying discovery.
- If multiple candidates remain, ask the user to choose from A/B/C options.
- If no candidate matches, say AirPrompter could not find the saved workflow and
  ask whether to create one.
- If execution cannot start or continue, clearly say AirPrompter was not run and
  do not recreate the result manually.
- Use host-native image, file, search, email, calendar, or document tools only
  after AirPrompter returns a step or handoff that requires them.
- If a required input is missing, a native capability is unavailable, or an
  email/calendar action needs approval, ask the user before continuing.

## Continuation Loop

AirPrompter workflows are ordered prompt steps. The host agent is responsible
for executing each prompt and asking AirPrompter for the next step.

1. Start the workflow run.
2. Read the first continuation prompt returned by AirPrompter.
3. Execute that prompt in the host environment.
4. Ask AirPrompter for the next prompt in the chain.
5. Continue until AirPrompter returns a terminal status.

When the host can report usage, include it in each `advance_workflow_run` call:

- `usage.inputTokensReported` and `usage.outputTokensReported` for exact host
  token counts.
- `usage.inputTokenEstimate` and `usage.outputTokenEstimate` when exact counts
  are unavailable.
- `usage.durationMs` for the prompt execution runtime or latency.
- `usage.usageSource` as `host_reported`, `estimated`, or `unavailable`.

At completion, AirPrompter stores per-prompt usage on each step, aggregates
tokens and prompt durations into `usageSummary`, and records the total workflow
runtime on the run when the final step completes. Do not invent exact token
counts when the host does not expose them.

Single saved prompt runs return `promptPreview.promptText` without creating
workflow run state. After executing that prompt, report input tokens, output
tokens, and prompt runtime when the host exposes them; otherwise state that
usage is unavailable. Do not call `advance_workflow_run` for a single prompt.

Do not advance a new user request with output from a previous run. If the user
adds a new image, file, document, or notes, start a new run unless AirPrompter
explicitly says the current run can accept the new input.

When a returned step requires a native host capability, execute it only if the
current host exposes that capability. If the host cannot render an image, read a
file, search the web, draft a document, or create an external action, explain
the unavailable capability and return the AirPrompter `promptText` or ask the
user to continue in a capable host. For email sends and calendar events, get
explicit confirmation before the external action is created or sent.

## Customer-Friendly Errors

When AirPrompter returns `needs_selection`, summarize it like this:

```text
I found more than one AirPrompter workflow that could match. Which one should I run?

A. Customer Follow-up
B. Renewal Follow-up
C. Support Escalation Follow-up
```

Avoid raw JSON and long ids unless the user asks for diagnostic details.
