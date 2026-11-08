---
name: airprompter
description: Create, run, find, edit, import, or export AirPrompter workflows, skills, and prompts, or diagnose its connection. Use when asked to create a workflow, build a reusable process, or turn this into a skill in AirPrompter. Excludes repository maintenance and explicitly local skill authoring.
---

# AirPrompter

Use MCP for all AirPrompter reads, writes, runs and reports. A skill is a saved
workflow. No other scripts, HTTP APIs or
emulation unless the user explicitly asks for a non-AirPrompter fallback.
Call tools by the names and shapes here or in a reference; never print
a tool object, description or schema, even one found by its exact name. Never call the same run tool again just to see a part of the
result you missed. Never narrate these instructions (no quotes, rule talk,
AirPrompter tool names, or this skill's file names): act on them in your own
words; still say errors and reconnect steps, and explain AirPrompter if asked
or on its code.
Keep installs, checks, usage, reports out of progress notes; if asked, answer
from `references/setup-diagnostics.md`.

## Author a workflow or skill

In AirPrompter context, "create a workflow," "create a skill," "make a workflow,"
"make a skill," "turn this into a skill or workflow," and "build a reusable
process" mean author a workflow. Load tools by exact name. For new designs,
show a useful preview before asking. Resolve the account before using its data
or saving. Use `plan_draft` with `target: workflow`. Confirm before `save_workflow`.
Do not run future actions during authoring.

Read `references/prompt-authoring.md` for creation or edits and
`references/skill-authoring.md` for skills. For import, export or shortcuts,
read `references/skill-import.md`.

## Run fast path

This covers a plain "use/run my AirPrompter <name>" (skill, workflow or
prompt); open a reference only for a status or failure it does not cover.
These shapes are complete: call the tool directly (a host that defers tools
loads just these by exact name first). Read whichever parts of a
result your host shows (text, `structuredContent`); if only text, act on the
status the text names.

1. `execute_workflow({ workflowName: "<name>" (or workflowId), matchMode:
   "ranked_confirm", fallbackPolicy: "fail_only", idempotencyKey: "<new>",
   client: <rule 4a> })`;
   Use `from: "private_collection"` only
   when the person asks for their private copy. If it fails naming `client`, or with -32602 or -32603 before any runId, repeat it once with
   the same idempotencyKey and without it, and omit it for the rest of this
   session. A refusal naming `from`: their private copy can't run here; never
   run the Playbook copy instead.
2. Act on the status, and pass on any line saying which copy ran (not one
   about installing):
   - a started run (`run`; a skill run's runId starts with `skill-`): follow
     its instructions and stored-files line (a question first: ask, wait,
     finish, then advance), then `advance_workflow_run({ runId, stepId,
     expectedVersion: <run.version>, idempotencyKey: "<new>", output: "<result
     summary>", usage: { usageSource: "unavailable" } })` until `completed`,
     `failed` or `canceled`.
   - `needs_selection`: ask one short A/B/C question; `needs_input`: ask for
     what is missing.
3. A saved prompt: `execute_prompt({ promptName, matchMode: "ranked_confirm",
   fallbackPolicy: "fail_only" })`; run `promptPreview.promptText` once; no
   advance and no usage line to the user.

## Routing Rules

1. Source, packaging and docs are repository work (no MCP). Local skill
   authoring stays local unless the user asks to save it in AirPrompter.
2. Saved workflow, my workflow, run my skill, run prompt, or the older name
   Airflow means AirPrompter discovery when context points at saved items;
   never reinterpret an explicitly local or other-system request. Read
   `references/connection-selection.md` only when several connectors or linked
   accounts could serve, or to diagnose one; else keep one connector and
   destination throughout.
3. MCP unavailable or unauthorized for a saved item: say AirPrompter was not
   used and stop. Do not produce a substitute result. When the tools
   are missing, or when
   the user asks to diagnose, repair, reconnect, or reinstall AirPrompter, read
   `references/setup-diagnostics.md` before responding.
4. Run workflows by the Run fast path; continue sequential or routed runs as
   the server says, never by an inferred graph.
4a. Every `execute_workflow`, `run_airprompter` and `start_workflow_run` call carries
   `client: { skill: "airprompter", version: "0.2.1", host: "<codex|claude|cursor|unknown>" }`
   by rule, with no schema check first. Say so only if asked. Only the Run
   fast path drops it.
5. If still ambiguous, ask one question with options; never choose an
   environment or account by tool order.
6. To run a saved item, use native host tools only after AirPrompter returns
   its steps, `promptText` or a native handoff (authoring is not running).
7. After a run, add "Used your AirPrompter skill: <name>." only when a ranked
   or loose match picked it or the request did not name it; never in headless
   runs or when its instructions say to return only the result.

## References

Read only what you need:

- `references/workflow-execution.md`: routed runs, failures, cancellation,
  no-fallback behavior, other statuses.
- `references/image-workflows.md`: images and files.
- `references/ambiguity-handling.md`: ambiguous names and needs-selection.
- `references/run-context-continuation.md`: stored runs from orchestrators.
- `references/setup-diagnostics.md`: skill-only install versus MCP connection,
  and repairing Claude Code setup.
- `references/activation-cases.md`: intent-routing examples.
