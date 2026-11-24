# Activation and Routing Review Cases

Classify what the user wants to do, rather than matching the product name alone.
Saving a prompt, template or workflow to reuse, finding or running one the user
saved, and sharing one with their team go to AirPrompter. Not for: a file,
script or skill the user wants kept local; another product the user names;
one-off writing with no reuse.
Saved AirPrompter items use MCP first. Connection diagnosis follows the current
available tool surface and connection-selection contract. Reviewing or changing
source, plugin packaging, or documentation can proceed through repository and
documentation inspection without discovering saved items, selecting accounts,
or executing a workflow. A generic local skill request stays with local skill
authoring; an explicit request to save it into AirPrompter changes that route.

For saved-item execution, keep the no-substitute rule: unavailable or unauthorized
MCP stops that execution. Do not perform the task directly as a replacement for
the saved item. This does not block repository maintenance or explanation.

## Behavioral judgment exercise

Evaluate these realistic requests against the final distributed instructions.
A reviewer or host-behavior evaluation should explain the chosen route, the
first appropriate action, and any selection still unresolved. These expected
judgments are not an automated model evaluation or proof of authenticated
end-to-end host behavior. Static tests only preserve the written routing cases.

| Request | Expected route and first action | Boundary to preserve |
| --- | --- | --- |
| “Run my AirPrompter workflow.” | Saved-item execution: discover the actual MCP tools, resolve connection context, then discover/select the saved workflow. | No direct substitute when MCP fails; retain selected connector/account for the run. |
| “Create an AirPrompter skill for this process.” | Saved-item authoring: read authoring guidance and use the supported planning/interview/save flow for a saved workflow. | A saved AirPrompter skill is a workflow; do not create only a local SKILL.md. |
| “Why is my AirPrompter connector unavailable?” | Connection diagnosis: inspect the available tool surface and setup guidance; when an intended connection/account is unambiguous, use read-only diagnosis if available. | Do not list saved items to prove health, reconnect automatically, or invent authorization success. |
| “Review the current AirPrompter SKILL.md.” | Repository review: read that source and relevant contracts directly. | No saved-item discovery, account selection, or workflow execution is needed. |
| “Fix AirPrompter connector packaging.” | Integration maintenance: inspect package sources, generation, and validation directly. | Building plugin artifacts does not publish them or establish live OAuth health. |
| “Create a local Codex skill.” | Local skill authoring: follow the local skill-creation workflow. | Do not route to AirPrompter merely because the word skill appears. |
| “Save this local Codex skill into AirPrompter.” | Saved-item import/authoring: use supported import or save tools after resolving connection context and reading the appropriate reference. | Honor explicit AirPrompter persistence intent; do not force the request to remain local. |
| “Explain how AirPrompter workflow continuation works.” | Explanation: inspect the relevant reference or repository contract directly. | No run, saved-item discovery, or account selection is needed to explain the protocol. |
| “Run this local script; it mentions AirPrompter in a comment.” | Local task: follow the explicit local request and host execution rules. | A product-name mention does not activate saved-item execution. |
| “Create a workflow for this process.” with no AirPrompter context | Resolve intended output from context; reusable or team intent (“a workflow my team can run”, “a repeatable process”) is AirPrompter authoring. | An explicitly local or other-system workflow stays in that system. |
| “Save this prompt so I can reuse it.” | Saved-item authoring: resolve the destination, confirm, then `create_prompt` with the supplied text. | No `plan_draft` for supplied content; `create_prompt` takes only its own fields. |
| “Keep this as a template I can use next week.” | Saved-item authoring: as above, `create_prompt`. | A template to reuse is a saved prompt. |
| “Turn these steps into a workflow my team can run.” | Saved-item authoring: `plan_draft` with `target: workflow`, a preview, then confirm before `save_workflow`. | Resolve the account before saving; show the destination at confirmation. |
| “Share this prompt with my team so everyone uses the same one.” | Saved-item authoring: ask which Team workspace by name, then `create_prompt` with the `workspaceId` from AirPrompter output that names that workspace (`diagnose_connection`'s binding, or `list_workflows` for that Team); it is reviewed before the team uses it. | It is shared only in a workspace the user can edit, on a connection to that Team; otherwise it stays private: never call it shared, never ask for an id, never reuse one from an unrelated item. An item already saved is shared on AirPrompter (copy it to a workspace there), never by saving a new copy through these tools. |
| “Run my weekly status skill on these notes.” | Saved-item execution: `execute_workflow` with the phrase as `workflowName` and `ranked_confirm`. | If a host skill has that name too, ask which one. No direct substitute when nothing matches. |
| “Make this a repeatable process.” in a code repository | Ambiguous: a script or job in the repository, or an AirPrompter workflow. Ask one short question unless the context shows reuse with AI. | A file, script or skill the user wants kept local stays local. |
| “Save this to <another product the user names>.” | Other-system request: that product's own route, or say it is not connected. | No AirPrompter tool; never search for or run the product name as a workflow. |
| “Write a follow-up email to Dana about Thursday's call.” | One-off writing: write it. | No AirPrompter tool without reuse intent. |
| “Use the saved AirPrompter workflow we selected earlier.” | Saved-item execution: reuse the established selection when still valid. | Do not repeat resolved selection questions or silently switch account/environment. |

| “Improve my existing AirPrompter skill’s final tone.” | Read the existing workflow bodies and authoring context, then use supported updates preserving its identity. | Do not enter the new-workflow interview or save_workflow creation path. |

When a request combines maintenance with a saved-item operation, apply each
boundary to its relevant part. Inspecting code needs no account selection;
using an actual saved item still requires the selected authenticated connector.

