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
- Represent placeholders as `{{placeholder_name}}`. Every placeholder is a
  required run input collected before step 1. AirPrompter stores no defaults,
  optional inputs, labels, or example values, so write fixed values directly
  into the prompt text and never promise a default.
- Keep placeholder names consistent and reusable.
- Include output expectations when the task needs a format.
- Avoid hard-coding one-off content unless the user is intentionally saving a
  one-off prompt.
- Stay at or below 4,000 characters, use a 3-8 word title, and include a
  one-sentence description.
- State output format, tone, and the tightest useful length or item limit.

## Create A Workflow

A workflow is an ordered set of prompt steps. When creating a workflow:

- Ask whether the user wants Personal Library or Team if both are available.
- For Team, ask for the workspace when not clear. Saving does not add the
  workflow to a playbook.
- Create or select prompt steps in the order they should run.
- Allow multiple steps with the same type, such as research, refine, research,
  audit, finalize.
- Ask before saving if the destination is ambiguous.
- Use one prompt when a single coherent responsibility can accomplish the North
  Star without becoming overloaded. Use a workflow when intermediate outputs
  add value.
- Keep each prompt or workflow step cohesive, bounded, independently testable,
  and responsible for one meaningful output or decision.
- Split at distinct expertise, tool, input, output-contract, evaluation, retry,
  or approval boundaries. Combine only pass-through, restatement, or
  reformatting steps. Never merge independent responsibilities merely to reduce
  step count. There is no fixed maximum.
- Give every step promptType, outputType, platforms, categories, and an explicit
  output contract. Give the workflow the final deliverable's outputType.
- Reference consumed prior output in prose; never use `{{previous_output}}`.

### AirPrompter planning and host authoring

Call `plan_draft` before authoring a new prompt or workflow. It deterministically
returns a step plan and a bounded set of questions, with saved preferences
already applied where possible. Present its unanswered questions verbatim as
A/B/C/D choices and collect letters plus any free text. Then call
`generate_draft` with the plan and answers. It returns the contract and
authoring brief for the calling agent; it does not write the prompt prose.

Author within the thresholds above, teach the chain back in plain language, and
apply corrections. Save once with `creationRouting.mode: host_planned` and a
one-paragraph `interviewSummary`. The planning and brief tools are read-only,
available on every tier, call no model, and consume no credit.

Use `improve_workflow` to inspect an existing saved workflow. It returns a
deterministic standards audit and structural questions without changing the
workflow. After the user accepts revisions, author them in the calling agent and
persist them through `update_workflow` or `update_prompt`.

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
