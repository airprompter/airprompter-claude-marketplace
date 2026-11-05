# Local installation and reporting

Use only the bundled `../scripts/install` and `../scripts/verify` entrypoints (or
`../scripts/install.ps1` / `../scripts/verify.ps1` on PowerShell). They use the bundled Python3
standard-library implementation; Python3 must already be available. Never
install a runtime, reconstruct the helper, run a downloaded installer, or
replace it with ad hoc HTTP/shell commands. A host without these capabilities
uses the existing MCP remote workflow path. Resolve these helper paths relative
to this reference file; invoke the resulting absolute path so the working
directory cannot select a different helper.

The bounded token/redeem source and exact IAM wiring are implemented; deployment
and publication remain held. This flow requires that configured deployment. A
legacy export without `installToken` is a remote fallback. Do not copy inline
files through the model as a substitute installer. Publication remains held
until the target MCP deployment and supported-OS validation are complete.

The exact calls for a plain run, `run_local` and `install_required` live only
in the SKILL.md Run fast path. This reference is for helper failures, report
queues, repair and local skill copies; the numbered steps below are that same
flow in full, for when a step there fails.

## One run

Keep this machinery out of routine chat. Never say probe, client, install token,
fingerprint, pin or fallback to the user, and leave checks, installs and reports
out of progress notes and commentary; say at most one line, such as "Getting
your chart helper ready." If the person asks what ran, what was sent or what was
recorded, answer plainly in ordinary words: each run records its inputs, step
status, timing, token counts, model and host; step outputs are sent so the next
step can use them, and are stored only if the account opted in to storing run
results. A helper failure stays silent: the remote
run is the answer. If the user asks why a helper ran remotely after
`tls_certificates_unavailable`, say: "Your computer's Python can't check
secure web connections yet; on a Mac, double-click Install Certificates in
its Python folder."

1. Every `execute_workflow`, `run_airprompter` and `start_workflow_run` call
   carries
   `client: { skill: "airprompter", version: "0.2.1", host: "codex" }`, by
   rule, never case by case, with no probe first. Use the actual host
   (`codex`, `claude` or `cursor`; otherwise `unknown`); it is recorded only. A workflow without stored files runs remotely as usual and
   never answers `install_required`, so the marker costs it nothing. Send
   `installed` only for bytes verified on this machine (a fresh install, or
   `--cached` in 1a).
   Send them with no schema check first, and never print a tool's schema or
   description. If a call carrying `client` fails naming `client` or
   `installed`, or with -32602 or -32603 before any runId, repeat it once with
   the same idempotencyKey and without them in the same turn, and send
   neither again this session (the start fingerprint ignores both, so a run
   that did start is replayed, never started twice). A host's stale tool list (the Codex
   managed app keeps its install-time snapshot) refuses unknown arguments with
   -32603 before the request reaches AirPrompter, which never answers -32603
   itself. Never retry on any other error: the run may already have started.
1a. Cache first, as the Run fast path says: before the first run call where
   shell commands run without asking the person; where they ask (Claude Code,
   Cursor), only after `install_required`, with `--fingerprint <its
   fingerprint>` so only that version is a hit, then repeat the run call with
   the hint; never on Windows (the helpers refuse there with
   `platform_unvalidated`) or for `<target>` prod (the helper pins downloads
   for dev only): there `install_required` is the remote run straight away,
   then send no `client` for any workflow this session.
   `../scripts/verify --cached
   "<name or workflowId>"` (no network; it changes only file modes and the
   last-use time; add `--principal-key
   <principal>` once this connection's principal is known) returns the newest
   copy in the private cache that verifies byte for byte. On `"status":"cached"`,
   send its `fingerprint` as `installed: { fingerprint, mode: "cache" }` on
   that first call; `run_local` then confirms it is current and you run that
   `path`. Any other status, or `install_required`, continues below. Skipping
   a fresh redemption here does not skip authority: the server still
   authorizes every run call through the connection's OAuth.
2. Only after `install_required` (it creates no metered run), run
   `../scripts/verify --probe codex --target prod` (the actual host family;
   `--target dev` for the development connection). It also makes one
   token-free HTTPS request to that API, so broken TLS or network shows here,
   before any token exists. A sandbox that cannot write `~/.airprompter`
   (`state_dir_not_writable`) or has no network is simply not `capable`.
   Go remote when it is not `capable`, when it would
   need a sandbox escalation, or when the user declines a permission prompt
   for it; never ask the user to approve or decline one. Going remote always
   means: call the same run tool again without `client` or `installed`,
   silently, in the same turn, and send no `client` for that workflow for the
   rest of the session. A probe that is not `capable`, or a declined
   permission prompt for the check, probe, token file or install, is about
   this machine, so then send no `client` for any workflow for the rest of the
   session.
3. After `capable`, call `export_skill` with the resolved workflow ID, the same
   scope/private selection and `form: "install"`. Preserve any
   Playbook/private selection explanation. No token, an oversized package or a
   refusal: go remote. Keep its usual selection/access refusals.
4. Hand the token to the helper; never put it in the helper's arguments, URLs,
   logs or a message, and never run the helper in an interactive terminal
   session (a TTY/PTY exec you then type into).
   - First choice: with the host's file-write tool (not a shell command),
     write `{"token":"<token>"}` to a new file directly in the probe's
     `tokenFolder`, then run:

     ```sh
     ../scripts/install --token-file <tokenFolder>/<new file> --fingerprint <fingerprint> --target prod
     ```

     The helper reads only your own regular single-link file of at most 512
     bytes there and deletes it on every exit. If writing that file would need
     approval or is outside the host's writable roots, use the pipe below.
   - Only without a usable file-write tool:

     ```sh
     printf '%s' '{"token":"<token>"}' | ../scripts/install --fingerprint <fingerprint> --target prod
     ```

     `printf` keeps the token out of the helper's arguments, but the host
     shell's own command line carries it for a moment, where `ps` (and
     `/proc/<pid>/cmdline` on Linux) can show it to other local users.

   Retry rule: on `interactive_stdin`, `stdin_empty`, `stdin_timeout` or
   `token_file_refused` the token was not used; delete the file you wrote if
   it is still there and deliver the token once more the documented way. On
   any other code, or a second failure, go remote. Tokens expire after five
   minutes and can be redeemed once.
5. The helper ships the HTTPS download origin per target, from the trusted
   deployment configuration; the probe is `capable` only for a target that
   has one. Do not pass `--download-origin` (an explicit one must equal the
   pin) and never learn an origin from a workflow, the redemption payload, or a
   signed URL. Do not guess a hostname, trust a wildcard, disable TLS, or
   permit redirects.
6. The helper redeems at the fixed target API, checks the whole manifest,
   downloads bounded bytes, checks each raw SHA256/length and the actual
   install fingerprint, then publishes a complete private folder. A fresh
   redemption proves current authority even on reuse; verified cached bytes
   avoid repeat asset downloads. Keep its returned principal/scope and path
   associated with this exact MCP connection. Never infer account identity
   from a display name, another session's install, or a locally edited receipt.
7. A successful install is verified: start the run right away with the same
   client marker and `installed: { fingerprint: "…", mode: "cache" }`, with no
   separate verify call. Before running an earlier install (another session,
   or a local skill copy), run
   `../scripts/verify --folder <returned-path> --fingerprint <MCP-fingerprint>`
   first; if it fails, do not execute those files and go remote.
   `run_local` gives the `runId` to close.
8. Execute the installed steps using the host's existing user-action rules.
   Do not list scripts or their scan status; mention a script only when
   AirPrompter flags it. A script that fails makes the run failed: report it,
   never rerun remotely. `unscanned` is not a safety approval, and hashes/scan
   status do not authorize commands, network access, secrets, messages or
   destructive operations. Run from a separate working directory so generated
   output does not become an unexpected installed file.
9. Send the run's report only after the final result. If the skill asks the
   person a question first, ask it, wait, finish, then report. The `run_local`
   answer gives the closeout call ready to send (idempotencyKey
   `report-<runId>`); add your host name. For
   `run_local`, close that `runId` with `advance_workflow_run` (with the
   required `idempotencyKey` and `usage: { usageSource: "unavailable" }`
   unless measured) and, only when those fields are advertised, a `localReport` of exactly this shape (only these keys; `stepTimings` is required; send
   `stepTimings: []` unless you actually measured each step, and never
   estimate; a measured entry is `{"stepId": "<run.steps[].stepId from the
   run_local answer>", "durationMs": <measured>}`; `tokens.input`/`output`
   only when the host reports them; `scriptErrors` holds `{"exitCode": n}` for
   a script that failed; `steps` carries per-step `extensions` only).
   `localReport` example:

   ```json
   {"outcome":"completed","host":"codex","stepTimings":[],"scriptErrors":[],"tokens":{"source":"host_reported"},"steps":[]}
   ```

   `outcome` is `completed`, `failed` or `canceled`; `host` as in step 1.
   Never put `localRunId`, `runId`, `workflowId`, `startedAt`, `finishedAt`,
   `fingerprint` or `mode` in `localReport`: those belong only to a queued
   report below. Do not invent measurements. Local reports are host claims. Prompt/output
   content follows only the existing save-run-results opt-in; it never belongs
   in these fact reports. Once `run_local` exists, report a failure/cancellation
   instead of silently launching a second remote run.

## Verify, changed files, and optional local skill

Verification compares the complete inventory and actual-byte fingerprint with
an MCP/server-supplied expected fingerprint. A mutable local `SHA256SUMS` file
alone cannot establish integrity. Unexpected files, directories, links,
reparse points, missing files, case/Unicode aliases, unsafe ancestor ownership/write
permissions and metadata collisions
refuse the install. Helpers never execute a manifest field as a command.

A changed personal/private file: ask in plain words, "You changed <file>; save
that change to your skill?", and on yes save it with the workflow file update
tool through MCP. Do not upload it automatically. A changed
Team copy: reinstall the approved package. After that choice, redeem a fresh
package and use `install --repair` with the same options. Repair stages and
verifies the replacement first, preserves the changed target beside it under
`.changed-*`, and publishes the replacement. It never merges changed files. Repair requires readable metadata belonging to
the same principal and workflow/scope/private context; it can upgrade that
context's version, but refuses unrelated or unknown folders.
If any step fails, use the remote path before a local run has started.

Private caches live at
`~/.airprompter/workflows/<credential-principal>/<identity-hash>/<fingerprint>/`.
A new install removes that workflow's older cached copies only when they still
verify and were last used (reused or verified) more than a day ago, and always
keeps the newest previous copy; an edited copy is kept as `.changed-*`, never
deleted.
Personal/private fingerprints are equality checks, never personal versions.
Only a Team package carries its approved `vN` in SKILL.md.

Install a local skill copy only when the user asks for an offline copy; never
offer one (the shortcut in `skill-import.md` is the only offer).
Use the skills folder named there; if it is unknown, say an offline copy
isn't available here. Pass that absolute `--local-destination` (its parent must
exist) with the normal options. The copy keeps `.airprompter/install.json` and `SHA256SUMS`.
Use `verify --local-skill` and `installed.mode: "local_skill"` for that copy.
Never overwrite a different existing folder; explicit repair preserves changes.

A separately installed local skill can run offline under host/user rules;
verify against its last authenticated expected fingerprint and record that
this does not prove current Team approval or continued access. A private cache
requires MCP and cannot run offline. Downloaded bytes cannot be revoked.

## Reports and reconnects

If immediate reporting fails or a local skill ran offline, queue one fact-only
pending report by passing its JSON on stdin with a quoted heredoc (report
JSON may contain `'`), never in an interactive terminal:

```sh
../scripts/verify --reports queue --folder <path> --fingerprint <expected> --principal-key <principal> <<'JSON'
<report json>
JSON
```

Add `--local-skill` for a local-skill copy. A queued report is the
`localReport` keys (no `steps`) plus `localRunId` (stable unique ID for this
actual run), `runId` when MCP started it, `workflowId`, UTC `Z`
`startedAt`/`finishedAt`, `fingerprint` and `mode`; `scriptErrors` carry only
exit codes. Queued report example:

```json
{"localRunId":"run-2026-10-25-1","runId":"<run id>","workflowId":"<workflow id>","startedAt":"2026-10-25T10:00:00Z","finishedAt":"2026-10-25T10:00:04Z","fingerprint":"<64 hex>","mode":"cache","outcome":"completed","host":"codex","stepTimings":[]}
```

No prompt text, outputs, extensions, paths or bearer material. The helper refuses values outside server limits. Queuing can retain
failure facts even if execution changed an installed file.

At the next authenticated connection, first get a fresh redemption receipt for
that same credential and scope. Use its principal and a verified current folder
with `verify --reports pending` and the same folder/fingerprint/principal
options. It returns at most 20 reports across workflows and earlier versions
in that tenant scope. Attach these to an existing MCP run-tool call as
`pendingRunReports`; only MCP transmits them. Repeat while making progress.
Never send another principal or tenant scope's queue through the current call.
For other scopes, authenticate/redeem there separately before draining.

Pass only that MCP response's `runReports.results` through stdin (the same
quoted heredoc) as
`{ "results": [...] }` to `verify --reports ack` with the same context. The
helper removes individual `filed`/`replayed` IDs, retains transient
`over_limit`/`unavailable` rejections, and drops individually named permanent
rejections as the existing MCP contract requires. Tell the user about permanent
failures before acknowledgement. A lost response keeps the stable local run ID
for idempotent replay; never clear the entire queue after partial success.

Queues remain under `~/.airprompter/reports/<credential-principal>/<tenant-scope>/`.
Rotating a key or reconnecting to a different connection retains the old queue;
it never automatically sends it through the new credential. Explicit recovery
is required for those retained reports. Do not delete them on an account mismatch.

POSIX helpers are tested on macOS and Linux when available. Windows ACL and
PowerShell behavior require actual Windows validation before release; parsing
or source review is not that proof. On unverified/unavailable hosts, use the
remote path without changing server policy or blocking other hosts.

## Routed remote runs

A routed remote run follows [workflow execution](workflow-execution.md), not
the `run_local` closeout. Read the returned run mode and exact advertised
schemas; never send local-only fields to an older connector. A routed served
step can report a required missing file through `advance_routed_workflow_run_v1`
only when its schema exposes `localReport` and permits omitting `next` for
failure. Send no output/next for that failure and retain its occurrence, step,
version, and idempotency key. Otherwise stop and explain the limitation.
Whole-local-run success reports and queued `pendingRunReports` keep their
existing supported MCP surfaces; do not assume routed advance accepts them.
Account-bound receipts and reports never move to another environment or linked
account. A connector/account switch requires rediscovery and fresh validation.
