# Activation and Routing Review Cases

Classify what the user wants to do, rather than matching the product name alone.
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
| “Create a workflow for this process.” with no AirPrompter context | Resolve intended output from context; do not assume a saved AirPrompter workflow. | An explicitly local or other-system workflow stays in that system. |
| “Use the saved AirPrompter workflow we selected earlier.” | Saved-item execution: reuse the established selection when still valid. | Do not repeat resolved selection questions or silently switch account/environment. |

| “Improve my existing AirPrompter skill’s final tone.” | Read the existing workflow bodies and authoring context, then use supported updates preserving its identity. | Do not enter the new-workflow interview or save_workflow creation path. |

When a request combines maintenance with a saved-item operation, apply each
boundary to its relevant part. Inspecting code needs no account selection;
using an actual saved item still requires the selected authenticated connector.

