# Prompt And Workflow Authoring

Use this reference when the user asks to create, write, invent, save, update, or
improve an AirPrompter prompt or workflow.

## Create A Prompt

Before saving a prompt, draft it as professional Markdown instructions.

Ask for missing information only when it changes the role, runtime inputs, or
save destination. If the role is ambiguous, ask one simple clarifying question
that helps identify the professional role the prompt should emulate.

The prompt should:

- State the role clearly.
- Include an initial research or inspection pass when that helps the role do
  higher-quality work.
- Ask whether the user wants runtime placeholders.
- Represent placeholders as `{{placeholder_name}}`.
- Keep placeholder names consistent and reusable.
- Include output expectations when the task needs a format.
- Avoid hard-coding one-off content unless the user is intentionally saving a
  one-off prompt.

## Create A Workflow

A workflow is an ordered set of prompt steps. When creating a workflow:

- Ask whether the user wants Personal Pro or Team if both are available.
- For Team, ask for the workspace and playbook when not clear.
- Create or select prompt steps in the order they should run.
- Allow multiple steps with the same type, such as research, refine, research,
  audit, finalize.
- Ask before saving if the destination or playbook is ambiguous.

## Update Prompts Or Workflows

When the user says something like "update the workflow I just created to make
the third prompt generate 50% fewer tokens", identify the likely target from
recent context, then use AirPrompter MCP update tools. If the target is unclear,
ask a short A/B/C selection question.

Use `update_prompt` when the requested change modifies prompt instructions,
including token efficiency, stronger final output, different output format,
placeholder behavior, role framing, or model guidance. Use `update_workflow`
only when changing workflow metadata, prompt membership, step labels, or step
order.

When the user asks to improve a workflow without naming a specific prompt, first
inspect the workflow with `get_workflow`, review the ordered steps, decide which
prompt or prompts control the requested behavior, and update those prompts with
`update_prompt`. For example, final-output quality usually belongs in the final
or synthesis prompt, while token efficiency may belong in research, reduction,
or finalization prompts.

Do not create a duplicate prompt or workflow when the user asked for an update.
