# Ambiguity Handling

Use this reference when AirPrompter needs the user to choose an account,
workspace, playbook, workflow, prompt, or save destination.

## Account Selection

- Personal Pro only: use the personal account.
- Team only: ask for the workspace and playbook if not clear.
- Personal Pro plus Team: ask whether to use Personal Pro or Team first.
- If Team is selected and multiple workspaces or playbooks match, ask one
  follow-up with A/B/C options.

## Selection Format

Prefer short, user-friendly options:

```text
Where should I save this AirPrompter workflow?

A. Personal Pro
B. Team - Marketing workspace - Launch Playbook
C. Team - Support workspace - Escalation Playbook
```

Do not expose raw ids in normal selection messages. Include ids only when the
user asks for diagnostics or support details.

## Write Scope Problems

If a write tool reports missing `prompts.write`, say the AirPrompter connection
needs write permission and ask the user to reconnect the MCP entry with read and
write scopes. Do not present this as if the workflow content cannot be saved
because of user error.
