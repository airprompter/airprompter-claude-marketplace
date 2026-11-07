---
name: airprompter
description: Create, run, find, edit, import, or export AirPrompter workflows, skills, and prompts, or diagnose its connection. Use when asked to make or build a workflow or skill in AirPrompter. Excludes repository maintenance and local skill authoring.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/verify *) Bash(${CLAUDE_SKILL_DIR}/scripts/install *) Read(~/.airprompter/workflows/**) Edit(~/.airprompter/tokens/**)
---

# AirPrompter

AirPrompter is the user's saved prompt and workflow system. Use MCP for every
read, write, run and report. No HTTP APIs, local scripts or emulation
unless the user explicitly asks for a non-AirPrompter fallback. The bundled helpers
authorize no workflow script or external action. A skill is a saved workflow.
Call tools by the names and shapes here or in a reference; never print
a tool object, description or schema, even one found by its exact name. Never call the same run tool again just to see a part of the
result you missed. Never narrate these instructions (no quotes, rule talk,
AirPrompter tool names, or this skill's file names): act on them in your own
words; still say errors and reconnect steps, and explain AirPrompter if asked
or on its code.
Keep installs, checks, usage, reports out of progress notes; if asked, answer
from `references/local-install.md`. Claude Code: for each new run request, invoke
this skill again (its helpers are pre-approved only in that turn).

## Author a workflow or skill

In AirPrompter context, "create a workflow," "create a skill," "make a workflow,"
"make a skill," "turn this into a skill or workflow," and requests to build
or set up either mean author a saved workflow. Load tools by exact name. Use
`plan_draft` for new designs, then draft, review and get approval before
`save_workflow` as the reference directs. Keep future actions in the
instructions; do not run them during authoring.

For creation or edits, read `references/prompt-authoring.md`; for a skill,
also read `references/skill-authoring.md`. For import, export or shortcuts,
read only `references/skill-import.md`.

## Run fast path

This covers a plain "use/run my AirPrompter <name>" (skill, workflow or
prompt); open a reference only for a status or failure it does not cover.
These shapes are complete: call the tool directly (a host that defers tools
loads just these by exact name first). Read whichever parts of a
result your host shows (text, `structuredContent`); if only text, act on the
status the text names. In code mode print both parts from the same call,
except `installToken`: never print it. `<dir>` is `${CLAUDE_SKILL_DIR}`; `<target>` is `dev` only for the
development connector, else `prod`. On `<target>` prod or Windows the
helpers never run: skip step 1; `install_required` is the remote run (no
probe); then no `client` this session.

1. Only where shell commands run without asking the person (a code-mode host;
   never Claude Code or Cursor): `<dir>/scripts/verify --cached "<name or
   workflowId>"`, plus `--principal-key <principal>` once an earlier install
   gave one. Only `"status":"cached"` gives a hint (`fingerprint`, `path`).
2. `execute_workflow({ workflowName: "<name>" (or workflowId), matchMode:
   "ranked_confirm", fallbackPolicy: "fail_only", idempotencyKey: "<new>",
   client: <rule 4a>, installed: { fingerprint, mode: "cache" } })`;
   `installed` only with a cached hint, and `from: "private_collection"` only
   when the person asks for their private copy. If it fails naming `client` or
   `installed`, or with -32602 or -32603 before any runId, repeat it once with
   the same idempotencyKey and without them, and send neither again this
   session. A refusal naming `from`: their private copy can't run here; never
   run the Playbook copy instead.
3. Act on the status, and pass on any line saying which copy ran (not one
   about installing):
   - `run_local`: follow `<path>/SKILL.md`, reading its other files from
     `<path>` only when it says to (work in the user's folder); run its scripts
     under your own approval rules. After the final result (a question first:
     ask, wait, finish), send the closeout call the answer gives, with your host
     name (`outcome` `failed` plus `scriptErrors: [{"exitCode": n}]` if a script
     failed). A failed script is a failed run: report it, never rerun remotely.
   - `install_required`: the remote run is step 2 again without `client` and
     `installed`, silently. If step 1 did not run, first
     `<dir>/scripts/verify --cached "<workflowId>" --fingerprint <its
     fingerprint>`: if cached, repeat step 2 with `installed` and continue as
     `run_local`. Otherwise `<dir>/scripts/verify --probe <host> --target
     <target>`; if `capable`: `export_skill` with the answer's `workflowId`,
     `form` and any `from`; write `{"token":"<installToken>"}`
     with the file-write tool to a new file in the probe's `tokenFolder`; run
     `<dir>/scripts/install --token-file <file> --fingerprint <fingerprint>
     --target <target>`; repeat step 2 with that fingerprint and continue as
     `run_local` with the install's `path`. In code mode do all of this in one
     cell, writing the token file from the variable (never a patch, an echo, or
     printed). Not `capable`, or a declined permission prompt for any of
     these: the remote run, and no `client` for any workflow this session. A
     needed sandbox escalation, no token, or an install or verify failure
     (after the one retry its hint allows): the remote run, and no `client`
     for that workflow this session.
   - a started run (`run`; a skill run's runId starts with `skill-`): follow
     its instructions and stored-files line (a question first: ask, wait,
     finish, then advance), then `advance_workflow_run({ runId, stepId,
     expectedVersion: <run.version>, idempotencyKey: "<new>", output: "<result
     summary>", usage: { usageSource: "unavailable" } })` until `completed`,
     `failed` or `canceled`.
   - `needs_selection`: ask one short A/B/C question; `needs_input`: ask for
     what is missing.
4. A saved prompt: `execute_prompt({ promptName, matchMode: "ranked_confirm",
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
- `references/local-install.md`: helper failures, report queues, repair, local
  skill copies (never for a plain run).
- `references/image-workflows.md`: images and files.
- `references/ambiguity-handling.md`: ambiguous names and needs-selection.
- `references/run-context-continuation.md`: stored runs from orchestrators.
- `references/setup-diagnostics.md`: skill-only install versus MCP connection,
  and repairing Claude Code setup.
- `references/activation-cases.md`: intent-routing examples.
