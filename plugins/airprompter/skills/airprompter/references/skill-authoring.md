# Create Or Improve A Skill

Use this reference when the user asks to create, make, build, or improve a
saved AirPrompter skill, or explicitly save a local skill into AirPrompter. A
generic local Codex skill request stays with local skill authoring. In AirPrompter a
skill IS a saved workflow: "create a workflow" and "create a skill" are the
same request and use the same tools. A standalone prompt is not a skill; a
skill with one job is its `SKILL.md` alone.

You are the author. AirPrompter plans, checks, and stores; it never writes the
skill's text for you, never calls a model to draft it, and never runs its
scripts.

## What A Skill Is Made Of

- `SKILL.md`: frontmatter `name` and `description`, then the instructions body.
  On its own it is an instructions-only skill (the whole job in
  `skill.instructions`, `prompts: []`; a Team workspace save keeps one step),
  and a lone `SKILL.md` that names a skill imports as one. On Free, once the
  skill limit is reached, it saves as a prompt for now.
- `references/<file>.md`: one saved prompt per step, for two or more separate
  responsibilities, a path the instructions choose, or a step that uses an app
  or has an outside effect.
- `scripts/...`: files the host runs (a converter, a lookup, a check).
- `assets/...`: templates, examples, schemas, or reference data.

## Steps

Read `prompt-authoring.md` for connection-scoped authoring context, body-read
requirements and the exact plan, draft and save calls. Route exactly as for a workflow: plan_draft and
generate_draft only when the user wants help designing new content;
save_workflow directly when the user supplies the content. If the user
supplied the content, go to "Verify Before Saving", confirm as
`prompt-authoring.md` rule 4 says, then "Saving".

1. When designing new content, call `plan_draft` as `prompt-authoring.md`
   rule 2 says (target `workflow`; a skill is a workflow), and ask its
   questions as that rule says. Show a short preview in the task’s words and propose one of
   the four shapes and say why. Its helpers question asks whether any step
   needs a script or an asset, and what each returns.
2. Call `generate_draft` with the plan as returned and the answers. Its brief carries the
   skeleton for each shape, filled with the plan's steps, the practices below,
   and the write path the server takes today.
3. Author the instructions, every reference, and any script or asset.
4. Verify (below) first, so the yes saves what you showed; then confirm as
   `prompt-authoring.md` rule 4 says and save once (see "Saving").
5. After the run words (`prompt-authoring.md` rule 9) and the person's answer
   to any shortcut offer, offer to run the skill once
   on a sample request with `execute_workflow`
   and `fallbackPolicy fail_only` to confirm it reads the right reference;
   never let a step that sends, posts or publishes, writes outside the
   working folder, or calls an outside service run without the user's
   go-ahead (the skill's own helper writing inside the working folder is
   not one).

## Shapes

- **Step by step**: Every step runs, always in the same order. AirPrompter
  can write `SKILL.md` from the steps (run mode `sequential`).
- **Choose a path**: The right step depends on what the person asks for.
- **Check and loop back**: A step's result must meet a bar before the skill
  moves on.
- **Start from scratch**: None of these fit, or the skill is mostly rules and
  judgment.

Any shape whose instructions you write yourself runs `agent_driven`.

## Best Practices

- **Name**: on the import door, frontmatter `name` becomes the AirPrompter
  title, so write the 3-8 word title there and name the folder in kebab-case.
  When AirPrompter exports the skill it writes the Agent Skills `name`
  (lowercase letters, digits and hyphens, at most 64 characters, equal to the
  folder name) and keeps the title in its metadata.
- **Description**: one sentence, in the third person, saying what the skill
  produces AND when to use it, in words the user would say ("Use when the user
  asks to ..."), at most 1,000 characters. Hosts pick a skill by its
  description.
- **Instructions**: loaded whole when the skill triggers, so keep them short.
  Role, Task (what to ask for first), Steps, Assets and Scripts (only when the
  skill has files), Example, Output. Say when to read each reference, by its
  exact `references/<file>.md` path AND title, its purpose, and the condition
  that calls for it. Keep
  references one level deep and use relative forward-slash paths. Do not tell
  the agent to read every reference in order unless every step always runs in
  that order.
- **References**: one responsibility and one output each, self-contained, at
  most 4,000 characters, with its required inputs, the output it hands back, and the receiving
  reference or instruction section stated in its text. Use
  `{{snake_case}}` only for values the user supplies every run; never
  `{{previous_output}}`.
- **Scripts**: on the line that names a script, say when to run it (or read
  it), what to pass in, and what it returns, prints or writes. Make it
  deterministic and safe to run twice (idempotent), exit non-zero with a
  one-line error on failure, and read secrets from environment variables or
  the host's credential store. Never write a key, token or password into a
  script or asset. Name what it needs in `skill.requires` (for example
  `runtime:python@3.11`, `bin:jq`). The host runs scripts under its own
  approval rules; AirPrompter stores scripts as data and never runs them.
- **Assets**: each one has a line saying when to use it. No secrets or
  personal data.

## References, Checkpoints, Loops, And Handoffs

Define every reference explicitly in the instructions: exact relative path,
title, purpose, when to read it, inputs, and output. Use the paths supplied by
the authoring brief or the existing skill. AirPrompter assigns filenames,
resolves title collisions, and preserves stored names across renames: do not
guess a path from a title or send `exportFile` as a client field. Reference
bodies belong in `prompts[]`, not as duplicate files in `skill.files`.
An instructions-only skill needs no reference list. Keep branch-specific
references conditional; a list of files does not make every file mandatory.

Write checkpoints as Markdown `- [ ]` items with observable pass conditions.
Mark a checkpoint complete only from evidence in the current run; track it
in the chat, never by updating the saved skill. At each handoff name the
producer (a reference or instruction section), the output passed on, the
receiver, and the condition that allows the receiver to start. State where
to pause for missing input or required user approval.

Only if the job needs a loop, name its entry, check, pass exit, fail/back
target, task-appropriate finite retry bound, and the outcome to report when
that bound is reached. Reset affected checkpoints after a repair; earlier
passes on changed work no longer count. Do not invent a loop for a one-pass
job, or retry an outside effect without checking its outcome and the required
authorization. These are authoring practices, not new server save refusals.

### Example (made up)

This fictional edit-and-review skill has two references with these exact
supplied paths. Its two-repair bound is illustrative, not a default for other
skills.

- references/draft.md — Draft: read first or after a failed review; input is
  the request plus any review findings; output is one revised draft.
- references/review.md — Review: read after Draft; input is that draft and
  the request; output is pass/fail plus concrete findings.

- [ ] Draft checkpoint: the draft addresses every requirement. Pass that
  draft and the request from Draft to Review only when both are available.
- [ ] Review checkpoint: no unmet requirement remains. On pass, hand the
  approved draft from Review to the Output section for delivery.

Loop: enter at Draft; check at Review. On failure, send Review's findings and
the draft back to Draft, clear both checkpoints, and review the repair again.
Allow at most two repairs. On exhaustion, stop and report the unresolved
findings. Pause if a required request detail is missing. This writing skill
has no outside action to approve.

## Verify Before Saving

- [ ] Every `{…}` part of a template is filled in.
- [ ] Every step, script, and asset is mentioned in the instructions or in the
  step that uses it.
- [ ] Every script line says what the script returns.
- [ ] "Step N" is cited only for steps that exist.
- [ ] Every script or asset path a step names is in `skill.files`, and every need in
  `skill.requires`.
- [ ] Every `{{variable}}` is a value the user supplies each run.
- [ ] Every reference uses its exact supplied path, with a read condition,
  inputs and output; handoffs name their payload, receiver and start condition.
- [ ] Checkpoints define their pass evidence, and any needed loop has an
  explicit target, finite bound, pass exit and exhausted outcome.

Check these yourself; reference definitions, checkpoint evidence, loops and
handoffs are author self-checks, not additional server save gates. "Step N" means reference N; number other procedure lines
without the word "Step". A `save_workflow` that carries the skill's own
instructions returns them as `skillFindings` and is refused on a Fix it adds.
The import door does not refuse on them: `preview_skill_import` lists them as
an instructions check, and a folder the person hands you imports as it is
(`skill-import.md`). `improve_workflow` skips the chain rules for a skill whose
instructions choose the reference.

## Saving

Confirm first as `prompt-authoring.md` rule 4 says. One write path:
`save_workflow`, once, with `creationRouting` as `prompt-authoring.md` shows
(`user_dictated` only for content the user dictated verbatim).

- **Step by step** (several steps that always run in order): `name`,
  `description` and `prompts[]` in order; helpers go in `skill.files` (`path`
  under `scripts/` or `assets/`, `role`, `content`) in the same call, needs in
  `skill.requires`, and each step that uses a file names its path, when to run
  it and what it returns. It stays sequential, and AirPrompter writes its
  instructions from the steps.
- **Its own instructions** (one job, or an agent that picks its references;
  any shape): the same `save_workflow`, `prompts[]` as the references (none
  for a one-job skill), and `skill: { runMode: "agent_driven", instructions: {
  content: <SKILL.md body> }, files, requires }`; it runs agent_driven for
  good. The save returns `skillFindings`: fix every Fix and save again.
- `preview_skill_import` and `import_skill` only for a folder the person hands
  you (`skill-import.md`); never write a folder to import it.

## Improve An Existing Skill

An edit never calls `plan_draft` or `generate_draft`.

1. For a content or output-quality edit, first call `get_workflow_prompts` and
   inspect the ordered bodies and handoffs as `prompt-authoring.md` describes.
   Use `get_workflow` for metadata and identifiers. Use `improve_workflow` for
   the supported audit; it does not replace reading the bodies.
2. Scripts and assets only when the change touches them:
   Only when exposed, call `get_workflow_files` for scripts/assets and use
   `update_workflow_files` with the returned `baseTreeHash`. If absent, explain
   that file editing needs a supported editor; never promise a hidden tool.
3. Author accepted changes after `get_prompt_authoring_context`. Change the
   prompt that produces the output with `update_prompt` (its step's prompt id
   from `get_workflow_prompts`, or `instructions.promptId` from `get_workflow`'s
   skill details); for an agent-driven skill's instructions, follow the
   in-place paragraph below. Change references through their own `update_prompt`
   calls, and structure through the supported workflow/step tools. Do not infer
   an instructions id merely from a first-step position.
4. Follow the Personal/Team rules in `prompt-authoring.md`. Personal prompts
   remain mutable and unversioned. Team workspace content edits create revisions
   for review and may need targeted step repinning; editing does not approve or
   release them. Team steps use the exposed targeted add/remove/move tools,
   rather than a full `steps` replacement. Follow refusal or copy guidance for
   noneditable Community items; never assume every shared item can be copied.
5. Run the supported `improve_workflow` check after editing. Where its audit is
   unavailable (including a My Private Collection path that says so), re-read
   supported bodies/metadata and check instructions, references and file mentions
   directly. Report verification limits; do not claim a complete audit.
6. For an agent-routed controller, use the dedicated save-then-adopt sequence in
   `prompt-authoring.md`; a successful prompt edit alone does not adopt routing.
7. Never import an edited folder to change a saved skill: that saves a second
   skill beside it. Do not introduce an extra readiness/approval stage beyond
   the existing planning, confirmation and authorized save flow.

The in-place edit, as AirPrompter's own `improve_workflow` remedy names it
(within the capability checks above): to change a saved skill in place, its
instructions with `update_prompt` on the instructions prompt id:
instructions.promptId in `get_workflow`'s skill details (always the workflow's
first step; `improve_workflow` also shows it for a skill in your library),
its references with `update_prompt` on their own prompt ids, its step list
with `update_workflow`, its scripts and assets with `get_workflow_files`, then
`update_workflow_files` from its baseTreeHash. `update_workflow` with
skill.instructions is the verified path for the instructions (it refuses a Fix
it adds); `update_prompt` is the fallback. `update_prompt` refuses at most a
Fix your edit adds to the instructions text and never checks references,
"Step N" or files, so run `improve_workflow` afterwards for the full check. For
a My Private Collection skill: `update_prompt` refuses at most a Fix your edit
adds to the instructions text and never checks references, "Step N" or files;
`improve_workflow` does not check a My Private Collection skill yet, so re-read
it with `get_workflow` after editing and check its instructions against the
practices yourself. This works for your own skills (your library or My Private
Collection) that are not published to Community; one published to Community is
refused: follow the refusal's message (make an editable copy). A Team workspace skill changes here into its draft: steps one
at a time (add_prompt_to_workflow, remove_prompt_from_workflow,
move_prompt_in_workflow), prompts with update_prompt, its instructions and
metadata with update_workflow skill, files with update_workflow_files; or edit
it on AirPrompter.

## Do Not

- Do not save a skill as a standalone prompt, or a standalone prompt as a
  skill; a one-job skill is its instructions alone, never padded with a
  reference that repeats them.
- Do not paste secrets into any file, and do not run a skill's scripts outside
  the host's normal user-approval rules.
- Do not write a skill folder to import it: save a skill you author with
  `save_workflow`.
