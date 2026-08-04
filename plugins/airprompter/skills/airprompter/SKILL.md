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
   was not used and stop. Do not produce a substitute result.
4. For workflow execution, use the strict execution path and set fallback policy
   to fail only when the tool supports it.
5. For ambiguous workflow, prompt, account, workspace, or playbook selection,
   show short A/B/C options and ask the user to choose.
6. Use native host tools only after AirPrompter returns workflow steps,
   `promptText`, or a native handoff; otherwise ask for missing input,
   capability availability, or user confirmation instead of substituting.

## MCP Boundary

MCP is the authenticated action layer. The skill only improves routing,
ambiguity handling, and host behavior. Any actual AirPrompter operation must go
through available AirPrompter MCP tools such as workflow discovery, workflow
execution, prompt creation, prompt updates, workflow creation, or workflow
updates.

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
