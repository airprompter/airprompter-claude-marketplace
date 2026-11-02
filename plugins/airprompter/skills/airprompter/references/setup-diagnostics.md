# Setup Diagnostics

Use this reference when AirPrompter tools are missing, or when the user asks
to diagnose, repair, reconnect, or reinstall AirPrompter in Claude Code.

## Readiness Layers

Treat the plugin, its bundled MCP server, the OAuth session, and the live
tool inventory as separate states. A Skill-only install cannot call AirPrompter.

1. Run `/plugin` and confirm the `airprompter` plugin is installed and enabled.
2. Run `/mcp` and confirm the bundled server `airprompter` points at
   `https://mcp.airprompter.com/mcp`; select it and authenticate if it has not signed in.
3. Run `diagnose_connection` before executing a saved workflow. Tool
   discovery alone does not prove authentication.
4. Start a new Claude Code session after installing or reconnecting so it
   loads the AirPrompter tools.

## Customer Installation

Install AirPrompter from its Claude Code plugin marketplace (`/plugin`), then
approve AirPrompter account authorization when Claude Code prompts. Customers
must not paste tokens, run `claude mcp add`, or register a second MCP server.

## Reconnect

If tools return Unauthorized after a completed login, run `/mcp`, reconnect
AirPrompter, and start a new session. Plugin reinstall and MCP
authentication are independent.

If the person only asked to run a workflow and did not ask for setup repair,
stop after reporting what is missing and how to fix it; do not produce a
substitute result.
