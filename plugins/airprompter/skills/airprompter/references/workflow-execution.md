# Workflow Execution

Use this reference for running saved AirPrompter workflows (skills), prompts,
or prompt chains. Resolve and retain the connector, environment, linked account,
and destination using [connection selection](connection-selection.md) first.
Tool names below are logical names: use the selected connector's actual tools
and advertised schemas, including its account argument only when required.

## Start and dispatch

- Use AirPrompter MCP discovery before native model, image, file, or search tools.
  Start from an explicit workflow ID; otherwise discover by title or description.
  Resolve remaining candidates with one concise selection question.
- Use strict execution and `fallbackPolicy: "fail_only"` when supported. If
  discovery, authorization, or execution fails, report what ran and what did
  not; stop without recreating the saved workflow's result manually.
- Execute only the saved prompt or native handoff returned by the server, under
  the host's existing action/approval rules. Missing inputs require clarification;
  unavailable capabilities require an accurate limitation, never invented results.
- After `start_workflow_run` (or the selected execution entrypoint), dispatch by
  the **returned** `continuation.nextTool`, instruction, status, and `nextAction`.
  `advance_workflow_run` means sequential; `advance_routed_workflow_run_v1`
  means routed. A routed start can return a compatibility `run` snapshot, so do
  not infer the engine from `run.steps` or ordered indexes. If dispatch is absent
  or contradictory, read status with the appropriate supported get tool; do not
  guess, advance, or execute another step.
- `needs_input` before a run starts: ask the returned `nativeExecution.questions`
  and retry the start with inputs as directed. Do not execute or advance.
  Once a run exists, follow its own retry/get instruction instead of starting
  another run. Unsupported continuation versions or unavailable required tools
  stop execution with a clear compatibility message; never fall back to another
  engine or connector.

## Sequential continuation

1. Execute the current returned `promptText` or supported native handoff once.
2. Call `advance_workflow_run` with its `runId`, current `stepId`, latest returned
   `run.version` as `expectedVersion` when supported, one stable `idempotencyKey`
   for this exact advance, output, and required `usage`.
3. Follow the next returned prompt/status until terminal. Outputless advance is
   only for explicit prompt-preview or operator-controlled continuation; an
   execution error is never successful output.

`get_workflow_run` reads state without advancing it. A status request is not
permission to execute or advance. Do not turn completed step snapshots into a
new execution instruction.

Report `usage.inputTokensReported` / `usage.outputTokensReported` for measured
counts, `inputTokenEstimate` / `outputTokenEstimate` for estimates, and
`usage.durationMs` when measured. Set `usage.usageSource` to `host_reported`,
`estimated`, or `unavailable`; do not invent counts or duration. Sequential
steps aggregate into `usageSummary`; exact total duration needs every step timed.

A single saved prompt returns `promptPreview.promptText` without workflow-run
state. Execute it once, report available usage, and never call either advance
method for it.

## Routed v1 continuation

The current routed contract is `contractVersion: 1`. Inspect the selected tool's
advertised schema before sending fields: repository changes can precede a
connector release. Do not reinterpret a future version as v1.

1. After a routed start, call `get_routed_workflow_run_v1` with `contractVersion`,
   the same `runId`, and any requested transient `inputs` / `previous_output` to
   obtain the authoritative routed state. The compatibility start's instruction
   also supplies the active IDs; the get response makes them structured.
2. Read `run.version`, `run.activeOccurrenceId`, `run.activeStepId`, and
   `continuation.occurrenceId` / `stepId`, `eligibleNextStepIds`,
   `eligibleNextSteps`, `completionAlternatives`, and `budget`.
   These are server state, never a graph for the host to reconstruct. Stop on
   missing or conflicting IDs. Execute only the current returned `promptText`
   when its native plan is executable (`direct` or supported `handoff_required`),
   inputs are resolved, and the run is running. Eligible next IDs authorize
   transition choices, not premature execution of their prompts.
3. After successful execution, call `advance_routed_workflow_run_v1` with
   `contractVersion: 1`, `runId`, active `occurrenceId`, active `stepId`,
   `expectedVersion: run.version`, a fresh `idempotencyKey`, actual `output`,
   available `usage`, and exactly one `next` choice:
   - `{ type: "step", stepId }` from `eligibleNextStepIds`;
   - `{ type: "complete", outcome }` from `completionAlternatives`, satisfying
     its authored terminal step and required steps;
   - `{ type: "paused", reason: "needs_input" }` for an intentional pause.
   Do not send irrelevant fields from other choices. Let the server validate
   completion prerequisites and finite bounds; never invent targets or outcomes.
4. Use each response's new occurrence and version. A later legitimate visit to
   the same saved step has a different occurrence: an old completed occurrence
   must not execute again. `budget.maxOccurrences`, `usedOccurrences`, and
   `remainingOccurrences` are authoritative. At zero remaining occurrences,
   do not request another step; use a valid returned completion alternative
   only if satisfied, otherwise stop for intervention. The server can pause at
   its bound; do not reset or increase the budget.

`get_routed_workflow_run_v1` reads status/rendering context; it does not complete
an occurrence. It **can atomically pause** on controller changes. It is not a
pure no-write diagnostic. Transient inputs/output are not persisted as prompt
content. If a get is needed after an advance, supply only the actual prior
output and requested inputs, never reconstructed server state.

## Stops, stale state, failures, and cancellation

- `completed`, `failed`, and sequential `canceled` are terminal: report the
  result/failure and stop. A routed completion outcome named `failed` or
  `rejected` can be a legitimate authored result; it is distinct from the
  host being unable to execute a step.
- `paused` never silently resumes. `controller_changed` requires re-adoption
  through the supported authoring sequence and a new run; no resume operation
  is currently available for other routed pauses. Ask for intervention.
- On `needs_input`, collect only missing inputs. Follow the returned retry
  instruction and retain its run/occurrence/version/key; if the advance already
  committed, get the new active prompt instead. Do not repeat the host action.
- On `version_conflict`, stale occurrence, or uncertain/timeout response, read
  current state on the same connector/account. Reconcile committed status and
  known host output before deciding whether to resend the **identical** advance
  with its original key. Never change a payload under a reused key. Never retry
  a completed step or blindly repeat an external action that may have succeeded.
  An idempotent AirPrompter advance does not make an email/send/service call
  idempotent. Verify its outcome using that service's supported reads; if still
  uncertain, stop and explain the uncertainty.
- If a step cannot be done, use the connected advance tool's `localReport`
  failure input **only when advertised**. For a missing required file, send
  `localReport: { outcome: "failed", steps: [{ extensions: {
  "airprompter.failure_reason": "file_unavailable" } }] }`, with no output;
  routed failure also omits `next` and retains all required active IDs/version/key.
  Other closed reasons are `execution_failed`, `input_missing`, and `other`.
  Follow the returned failure instructions. The current repository supports
  this routed failure extension, but older connectors require `next` and lack
  `localReport`: on those, stop and tell the user why, without fabricated output
  or a pretend success/completion transition. Do not retry an uncertain external
  action to satisfy a generic retry rule. A recoverable missing input or a
  legitimate result such as failing tests is not automatically a failed step.
- On cancellation, stop host execution immediately. For supported sequential
  runs call `cancel_workflow_run` with `runId` and latest `expectedVersion`,
  then confirm the returned status; on a conflict, read and reconcile first.
  The current routed v1 contract has no canceled status or cancel operation,
  and `cancel_workflow_run` does not dispatch routed runs. Do not claim routed
  cancellation succeeded or submit routed IDs to the sequential endpoint.
  Explain that host execution stopped but the server run remains in its last
  state. Use future cancellation support only when its actual contract says so.
- Do not reuse previous-run outputs for a new request. New images, files, or
  notes start a new run unless the current server response explicitly accepts
  them. A failed/terminal run is never restarted merely to hide a failure.

## Stored files and local execution

The SKILL.md Run fast path sends the `client` marker and handles `run_local`
and `install_required`; read [local installation](local-install.md) only for a
helper failure. Probe and verify installed bytes before starting a metered
local run; helper failure before start uses the existing MCP remote path. Keep the selected
connector/account and account-bound receipts through reporting. Never substitute
an invented script for a stored one. Text steps that need no file can run;
a step that needs an unavailable file follows the failure path above.

For remote file links, use `get_workflow_files` only when exposed. Save/download
unchanged bytes in the server-directed workflow folder under host permissions;
refresh expired links through MCP. Respect the run's Team tree binding: a
changed tree is unavailable for that run. If no file tool exists, stop only
when the current step needs a file you cannot obtain.

`run_local` keeps its existing `advance_workflow_run` + `localReport` closeout,
not the routed remote-transition payload. Follow the returned run mode and
advertised fields; do not attach whole-local-run success reports to routed
advance (its `localReport` only reports a failed served step). Once a local
run exists, report failure/cancellation or queue its account-bound facts as
[local installation](local-install.md) describes; do not silently start a
second remote run. Never send `pendingRunReports` to a tool lacking that field.

## Behavioral review cases

These are host judgment cases, not evidence of authenticated execution:

| Situation | Required decision |
| --- | --- |
| Sequential nextTool and a valid current prompt | Execute once, sequential advance with output/usage/key. |
| Routed nextTool with a compatibility snapshot | Routed get, then current occurrence; never sequential advance. |
| Routed success with an eligible target and remaining budget | Advance exact occurrence/version with that target; execute only the new returned prompt. |
| Completed/failed run or unsupported contract version | Stop; no further step or fallback. |
| Stale occurrence after a send timed out | Read/reconcile; never resend the outside effect blindly. |
| No remaining occurrences and unmet completion prerequisite | Stop for intervention; no invented completion or budget reset. |
| Required script missing on an older routed connector | Stop with limitation; no output or synthetic next. |
| User asks only for run status | Get status; no host step execution or advance. |
