# Skill Import

Use this reference when the user asks to import a skill, SKILL.md, or a public
skill link into AirPrompter, or to install a host skill that runs a saved
AirPrompter workflow. To create or improve a skill, read
`skill-authoring.md`; a skill you author saves with `save_workflow`, never
through this import.

## Required Behavior

- Use AirPrompter MCP. Do not recreate the skill as a local prompt chain.
- Prefer `files[]` when the host already has skill markdown.
- Use `sourceUrl` for a public skill link.
- Call `preview_skill_import` first. Show fitness notes (`importable`,
  `adapted`, or `skipped`) and unresolved references.
- Import the files as they are: show the preview's notes and instructions
  check, and change the person's files only if they ask. An import never goes
  through the authoring checklist.
- After the user confirms, call `import_skill` with the same files or URL.
- For an existing workflow, call `export_workflow_skill` with `workflowId`.

## After A New Save Or Import

After a NEW save (`save_workflow`, `create_workflow`, `create_prompt`, `save_prompt_from_output`) or an import, never after an in-place edit:
pass on the result's `Tell the person:` sentence when present; otherwise say:
'Next time just say: use my AirPrompter <name>.'
Shortcut offer: Claude Code/Cursor once after save/import, others only on
request (Shortcuts, below), in the same message as those run words. Offer a
test run only after the person answers it (one question per message); on
other hosts, with the run words.

## Pointer Skills

A pointer skill is a thin host `SKILL.md` bound to a created `workflowId`.

1. Call `execute_workflow` with that `workflowId` and `fallbackPolicy fail_only`.
2. If AirPrompter is disconnected or unauthorized, stop and say AirPrompter was
   not used.
3. Read [workflow execution](workflow-execution.md). Execute the returned saved
   prompt once and dispatch sequential or routed continuation from the returned
   tool/version; retain the connector/account until terminal. Never blindly
   repeat an outside effect after a stale or uncertain advance.

The server does not write `~/.cursor/skills`. The host writes one only after
the user says yes to the shortcut offer.

## Shortcuts

A shortcut is one pointer file in the host's user-level skills folder; there
are no project-folder shortcuts at all.

Skills folder: Claude Code `~/.claude/skills`, Cursor `~/.cursor/skills`, Codex `$CODEX_HOME/skills` (when set), then `~/.codex/skills`. Any other host: skip silently.

- Hosts that ask the person before each write (Claude Code, Cursor): right
  after a save or import, offer once, in the same short message as the run
  words (run words first): "Want me to add a shortcut so you can just say 'do
  my expense report' next time?" Never run a check first; the person's yes
  covers the one write prompt.
- Every other host: offer only when the person asks ("can I just say X next
  time?"). Write directly, trying the folders above in order; never request
  an escalation.
- If the write fails or is declined, say only: 'I couldn't add a shortcut
  here; you can still say "use my AirPrompter <name>".' Always say the
  skill's display title (the new one after a rename), never a folder slug.
- Give the run words (After A New Save Or Import, above) and any shortcut
  offer in one short message, run words first.
- At most once per skill per conversation, never automatically, never on a
  later run unprompted. Do not ask again after a no.

A same-named skill in a project folder (`.agents/skills`, `.claude/skills`,
`.cursor/skills` or any host's project skills folder, usually tracked in git)
gets no shortcut and no swap, silently. If the person explicitly asked for a
shortcut, say only: "This project already has its own copy of this skill, so
I left it as it is." Only when a
folder of that name sits in the user-level skills folder above (for example the
user imported from it), ask once instead: "You also have a copy of this skill
on this computer. Want me to swap it for a shortcut so you always get the
version saved in AirPrompter? Your copy goes to the Trash, so you can get it
back." Swap only on a clear yes to that question (anything vaguer is a no),
never silently: move the old folder to the Trash; on a host without a Trash,
to `~/.airprompter/replaced-skills/<name>-<UTC timestamp>/` (create it 0700);
if neither works, do not swap. Never delete it. If the old folder is a
symlink, move the link, never its target. Never touch any other folder, such
as the user's own source or project folders.

On yes, write this one pointer file directly at
`<skills folder>/<name>/SKILL.md` (create missing folders with `mkdir -p`);
stage nothing anywhere else. Never install the returned package files as the
shortcut: a full copy runs stale, without AirPrompter.

```markdown
---
name: <name>
description: "<stored description> Use when the user says '<phrase>'."
---

Shortcut to the user's AirPrompter skill "<skill name>". Run it through AirPrompter: execute_workflow {workflowId: "<workflow id>", fallbackPolicy: "fail_only"}, then follow the run. Never do the task from this file.
```

- `<name>`: the folder name in the returned package path (`<name>/SKILL.md`),
  else the skill name in lowercase letters, digits and hyphens (at most 64).
- `<stored description>`: the skill's saved description. Strip `"`, `\` and
  control characters from it, from the phrase and from the skill name; keep
  the description at most 1,000 characters.
- If the skills folder resolves inside a git repo
  (`git -C <resolved folder> rev-parse --git-dir` succeeds, e.g. a dotfiles
  symlink), add the shortcut's path to that repo's
  `git rev-parse --git-path info/exclude` silently; skip if that fails.
- Never overwrite anything else, and never claim a shortcut that was not
  written inside that skills folder. After writing, say only: 'Done. From
  your next conversation, just say "<phrase>".' Never give the path.

## Do Not

- Do not treat importing an existing skill as `plan_draft` / `generate_draft`
  interview UX; authoring a new one is (see `skill-authoring.md`).
- Do not invent `{{previous_output}}` placeholders.
- Do not fetch private-network hosts.
- Do not substitute a local rewrite when import or execution fails.
