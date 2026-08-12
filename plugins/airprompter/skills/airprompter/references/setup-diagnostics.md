# Setup Diagnostics

Use this reference when AirPrompter tools are missing, or when the user asks to
diagnose, repair, reconnect, or reinstall AirPrompter in Codex.

## Customer Install Rule

For the official AirPrompter plugin, installation comes from the universal
plugin directory shared by ChatGPT and Codex. The host registers the bundled
MCP connection and prompts the customer for AirPrompter OAuth during install.
Do not ask a customer to run `codex mcp add`, edit `config.toml`, add a Git
marketplace, or install a separate MCP entry.

If an official-directory install is present but tools are unavailable, use the
host's Plugins or Connectors UI to reconnect AirPrompter OAuth, then start a new
task. If the host still does not expose the bundled tools, report a plugin-host
integration failure for support; do not turn internal CLI repair into the
customer onboarding path.

## Local Development Readiness Rule

For private dev and local-marketplace installs, do not infer MCP readiness from
the AirPrompter skill being present or from
`codex plugin list` showing the plugin as installed. The plugin, skill, MCP
registration, and OAuth session are separate states. A healthy Codex setup must
have both the plugin and the matching MCP server entry.

Choose the identity from the installed plugin:

- `airprompter-dev@airprompter-dev` uses server `airprompter_dev`, URL
  `https://mcp.dev.airprompter.com/mcp`, and OAuth resource
  `https://mcp.dev.airprompter.com`.
- `airprompter@airprompter` uses server `airprompter`, URL
  `https://mcp.airprompter.com/mcp`, and OAuth resource
  `https://mcp.airprompter.com`.

## Codex Local Diagnostic And Repair

1. Run `codex plugin list` and confirm the expected plugin is installed and
   enabled.
2. Run `codex mcp get <server-name>`. If it succeeds with the expected URL, the
   MCP server is registered. Do not claim OAuth is healthy from plugin status
   alone.
3. If the MCP entry is missing and the user explicitly asked to repair setup,
   run:

   ```text
   codex mcp add <server-name> --url <mcp-url> --oauth-resource <oauth-resource>
   ```

   This may start OAuth automatically. If authorization does not finish, run:

   ```text
   codex mcp login <server-name> --scopes prompts.read,prompts.write
   ```

4. Run `codex mcp get <server-name>` again and confirm the expected URL.
5. Start a new Codex task before testing an AirPrompter workflow because a
   running task's tool inventory is fixed when that task starts.

Prefer the Codex CLI over editing `config.toml` directly. Never print OAuth
codes or tokens. If the user only asked to run a workflow and did not authorize
setup repair, stop after reporting the missing MCP registration and the exact
repair command; do not generate a substitute workflow result.
