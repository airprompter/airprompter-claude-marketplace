# Skill Import

Use this reference when the user asks to import a skill, SKILL.md, or a public
skill link into AirPrompter, or to install a host skill that runs a saved
AirPrompter workflow.

## Required Behavior

- Use AirPrompter MCP. Do not recreate the skill as a local prompt chain.
- Prefer `files[]` when the host already has skill markdown.
- Use `sourceUrl` only for an allowlisted public skill link.
- Call `preview_skill_import` first. Show fitness notes (`importable`,
  `adapted`, or `skipped`) and unresolved references.
- After the user confirms, call `import_skill` with the same files or URL.
- After a successful import, offer the returned pointer `SKILL.md` files.
- For an existing workflow, call `export_workflow_skill` with `workflowId`.

## Pointer Skills

A pointer skill is a thin host `SKILL.md` bound to a created `workflowId`.

1. Call `execute_workflow` with that `workflowId` and `fallbackPolicy fail_only`.
2. If AirPrompter is disconnected or unauthorized, stop and say AirPrompter was
   not used.
3. Execute returned `promptText`, then `advance_workflow_run` until terminal.

The server does not write `~/.cursor/skills`. Give the user the file contents
and let them install the pointer locally if they want.

## Do Not

- Do not treat a skill import as `plan_draft` / `generate_draft` interview UX.
- Do not invent `{{previous_output}}` placeholders.
- Do not fetch off-allowlist URLs or private-network hosts.
- Do not substitute a local rewrite when import or execution fails.
