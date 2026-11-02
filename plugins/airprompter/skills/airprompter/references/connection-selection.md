# Connection Selection and Continuity

Read this before a saved-item operation or authenticated connection diagnosis
when connector or account selection is unresolved. Repository maintenance,
packaging review, and documentation explanation do not require account selection.

## Select three independent dimensions

1. **Environment and connector:** discover the actual available AirPrompter tool
   surface: use the tool names and connection metadata the host already shows
   (never print schemas).
   Tool namespaces vary by host; do not assume a fixed prefix. Establish which
   connector is development or production from explicit metadata, registered
   endpoint, or the user's established context. Never select an environment
   because its matching tool appears first, and never infer production from an
   unqualified tool name alone.
2. **Linked account:** use the account explicitly named by the user or already
   selected in this session for that connector. Inspect the selected tool's
   account contract: the managed connector wrapper can require `link_id` selected
   from its advertised accounts. Direct MCP tools have no wrapper account
   argument; do not add `link_id` to a schema that does not accept it. A wrapper
   link is distinct from the server's diagnostic `binding.connectionId`.
3. **Destination:** resolve Personal Library versus Team, then the organization,
   workspace, or Playbook from the request, session context, and server selection
   response. A Team destination does not select a linked account or environment.
   A Personal destination does not imply a different account. Use only scopes
   supported by the selected connection and operation.

If exactly one compatible connection/account exists and nothing conflicts with
user intent, retain it without an extra question. Explicit user instructions
and established session context resolve selection when they identify an available
compatible option. If environment or account still has multiple plausible
choices, ask **one concise selection question** with available friendly labels,
combining environment and account choices when needed. Do not silently probe
several accounts, read customer items to guess ownership, or switch to another
account after an authorization failure. If the named connection/account is
unavailable, report that mismatch rather than choosing another one.

## Retain the binding

Keep a session-local association of the selected connector/environment, linked
account when applicable, and resolved destination. Use that same association for
discovery, reads, writes, execution, status reads, continuation, cancellation,
and reporting. Bind every run identifier, local-run report, redemption receipt,
and other account-bound response to the connection/account that returned it.
Never transfer a run identifier or account-bound receipt to another connector
or linked account, even when workflow titles or resource identifiers match.
Do not put tokens, account IDs, workspace IDs, receipts, or other customer-specific
values in distributed plugins; keep those values only in the authorized session.

After an intentional account/environment switch, re-discover available tools,
validate the selected account schema and connection context, and resolve the new
destination before further operations. Previously selected item IDs, runs, and
receipts retain their original binding. A request to continue an old run must use
its original connection/account; if unavailable, stop and explain the mismatch.
A switch never authorizes migrating an old run into the new connection.

## Verify the selected connection when appropriate

Use read-only `diagnose_connection` on the selected connection after OAuth,
when verifying first use, when investigating connection failure, or when a
switch leaves connection context uncertain. The direct MCP contract accepts
an empty argument object; a managed connector wrapper may additionally require
its advertised `link_id`. Never copy an example account value from a plugin.

Inspect returned `status`, `code`, checks, scope, and binding fields. A failed
or unauthorized result is not successful authorization. An ambiguous binding
requires resolving the context before scoped operations; a diagnostic sibling
count does not by itself choose a different linked account. `binding.staleness`
is diagnostic and never independently blocks calls. Stop on a contradictory
environment or destination and resolve it before reading or changing saved items.

Tool visibility, plugin installation, skill presence, and MCP registration are
separate from successful authorization. Package validation does not prove OAuth
or live MCP health; a healthy MCP connection does not prove current plugin
content. Reinstalling a plugin and reconnecting an account are separate actions
unless the host explicitly combines them. Diagnose before suggesting the repair
appropriate to the failed state; do not reconnect or change credentials without
the user's authorization.

## Behavioral review cases

These cases are a host-behavior review rubric, not executable connection tests.
Static regression checks protect the written contract; they do not prove model
routing, authenticated health, or host execution.

| Case | Expected behavior |
| --- | --- |
| One connection, one account | Use it when compatible; no redundant selection question. |
| Production, multiple accounts | Use the established account; otherwise ask one question before customer reads or writes. |
| Development plus production | Honor explicit environment/session context; otherwise ask, regardless of discovery order. |
| Explicit selection | Retain the named available environment/account across all operations. |
| Ambiguous selection | Ask one combined environment/account question; perform no cross-account probing. |
| Cross-connection continuation | Refuse to transfer the old run or receipt; use its original binding or stop. |
| Direct MCP without wrapper | Use its exact schema; never inject `link_id`. |
| Authorization failure | Report failure on the selected connection; do not hop to another account. |
| Intentional switch | Re-discover and validate; old runs remain bound to their original connection. |
