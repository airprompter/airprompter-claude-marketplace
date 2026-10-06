---
name: airprompter
description: Use when the user asks to use AirPrompter, air prompter, airprompter, airpromter, airprompt, Airflow, airflow, a saved workflow, a saved prompt, run prompt, execute prompt, create prompt, write prompt, invent prompt, create workflow, or update workflow.
---

# AirPrompter

AirPrompter is the user's saved prompt and workflow system. Treat prompts and
workflows as server-authored instructions for how the host agent should do work
better. Use the AirPrompter MCP server for authenticated reads, writes, and
workflow runs. Do not call AirPrompter HTTP APIs, use local scripts, or emulate a
saved workflow unless the user explicitly asks for a non-AirPrompter fallback.

## Routing Rules

1. If the user says AirPrompter, air prompter, airprompter, airpromter, or
   airprompt anywhere in the request, use AirPrompter MCP first.
2. If the user says Airflow, airflow, saved workflow, my workflow, use workflow,
   run workflow, execute workflow, run prompt, execute prompt, or use prompt,
   strongly prefer AirPrompter MCP discovery before doing the work directly.
3. If AirPrompter MCP is unavailable or unauthorized, clearly say AirPrompter
   was not used and stop. Do not produce a substitute result. On Codex, or when
   the user asks to diagnose, repair, reconnect, or reinstall AirPrompter, read
   `references/setup-diagnostics.md` before responding.
4. For workflow execution, use the strict execution path and set fallback policy
   to fail only when the tool supports it.
5. For ambiguous workflow, prompt, account, workspace, or playbook selection,
   show short A/B/C options and ask the user to choose.
5a. For a NEW multi-step workflow, call `plan_draft` to get the deterministic
   step plan and bounded interview, ask its unanswered questions verbatim,
   then call `generate_draft` with the plan and answers to get the authoring
   brief. Author and review each prompt in the calling agent, teach the chain
   back, then call `save_workflow` ONCE with `creationRouting.mode:
   host_planned` and a one-paragraph `interviewSummary`. These planning tools
   are read-only, available on every tier, call no model, and consume no
   credit. Use `improve_workflow` for a read-only deterministic audit of an
   existing workflow; persist accepted revisions separately through
   `update_workflow` or `update_prompt`. Only content the user dictated
   verbatim uses `creationRouting.mode: user_dictated`; headless agents use
   `creationRouting.mode: agent_autonomous` with complete per-prompt
   promptType, outputType, platforms, and categories.
6. For saved prompt/workflow EXECUTION, use native host tools only after
   AirPrompter returns workflow steps, `promptText`, or a native handoff. This
   does not prohibit host-side AUTHORING under rule 5a.

## MCP Boundary

MCP is the authenticated action layer. The skill only improves routing,
ambiguity handling, and host behavior. Any actual AirPrompter operation must go
through available AirPrompter MCP tools such as workflow discovery, workflow
execution, prompt creation, prompt updates, workflow creation, or workflow
updates.

## Authoring Thresholds

Before saving a prompt or workflow, verify all of these without a backend-model
call:

- Keep every prompt at or below 4,000 characters.
- Give every prompt a 3-8 word title and a one-sentence description.
- Use `{{snake_case}}` only for values that change each run; never use
  `{{previous_output}}`.
- State the output format, tone, and a tight length or item limit inside every
  prompt.
- Use one prompt when a single coherent responsibility can accomplish the North
  Star without becoming overloaded. Use a workflow when intermediate outputs
  add value.
- Keep each prompt or workflow step cohesive, bounded, independently testable,
  and responsible for one meaningful output or decision.
- Split at distinct expertise, tool, input, output-contract, evaluation, retry,
  or approval boundaries. Combine only pass-through, restatement, or
  reformatting steps. Never merge independent responsibilities merely to reduce
  step count. There is no fixed maximum.
- When a step consumes earlier work, reference that result in prose and state
  the producing step's output contract.
- Supply promptType, outputType, platforms, and categories for every workflow
  prompt, plus the workflow-level outputType.

## References

Read only the reference needed for the current task:

- `references/workflow-execution.md` for running workflows, airflows, prompts,
  continuation loops, and no-fallback behavior.
- `references/prompt-authoring.md` for creating or updating prompts and
  workflows from user instructions.
- `references/image-workflows.md` for image, file, or host-native generation
  workflows.
- `references/ambiguity-handling.md` for account, workspace, playbook, prompt,
  workflow, and needs-selection responses.
- `references/run-context-continuation.md` for consuming a shared stored-run
  context from orchestrator hosts and continuing stored runs.
- `references/setup-diagnostics.md` for distinguishing a skill-only install
  from a registered MCP connection and repairing Codex setup.
- `references/skill-import.md` for importing SKILL.md packs or public skill
  links into AirPrompter workflows and installing pointer skills.
