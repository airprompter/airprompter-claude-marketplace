# Ambiguity Handling

Use this reference when AirPrompter needs the user to choose an account,
workspace, playbook, workflow, prompt, or save destination.

## Connection and Destination Selection

Read `connection-selection.md` in this directory for environment, connector,
linked-account selection and continuity before selecting customer resources.
Resolve those independently from Personal/Team/workspace/Playbook destination.
Use explicit instructions and established session context before asking anything.

- Use the server's supported destination selection response and returned IDs.
  Do not assume Personal Library means a separate "personal account" or that
  every Team operation needs a Playbook.
- If the requested destination is unresolved, ask one concise question using
  available friendly labels. Reuse a prior selection when it remains valid.
- If several workspaces or Playbooks match, ask only for the remaining choice;
  do not repeat account or environment questions already answered.
- Respect missing permissions or unsupported destinations; do not silently fall
  back to another account, Team, or Personal Library.

## Selection Format

Prefer short, user-friendly options:

```text
Where should I save this AirPrompter workflow?

A. Personal Library
B. Team - Marketing workspace - Launch Playbook
C. Team - Support workspace - Escalation Playbook
```

Do not expose raw ids in normal selection messages. Include ids only when the
user asks for diagnostics or support details.

## Write Scope Problems

If a write tool reports missing `prompts.write`, say the AirPrompter connection
needs write permission. Explain that reconnecting with the required read and
write scopes is a separate user-authorized repair; do not reconnect automatically. Do not present this as if the workflow content cannot be saved
because of user error.
