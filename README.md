# AirPrompter Claude Marketplace

This repository publishes the AirPrompter Claude Code plugin marketplace.

Install the marketplace:

```bash
claude plugin marketplace add airprompter/airprompter-claude-marketplace
```

Install the plugin:

```bash
claude plugin install airprompter@airprompter
```

Inside a Claude Code session, the equivalent commands are
`/plugin marketplace add airprompter/airprompter-claude-marketplace` and
`/plugin install airprompter@airprompter`.

AirPrompter uses the hosted MCP server configured in
`plugins/airprompter/.mcp.json`. After plugin installation, Claude prompts for
the AirPrompter MCP OAuth connection on first tool use; run `/mcp` to
authenticate or reconnect at any time.
