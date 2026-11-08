# AirPrompter

AirPrompter connects Claude to your saved prompt and workflow library. Create,
run, and improve reusable multi-step AI workflows, and save them for repeatable
runs across your AI tools. You need an AirPrompter account, and Claude asks you
to sign in the first time it uses AirPrompter.

## What this plugin contains

- `.mcp.json` registers the hosted AirPrompter MCP server at
  `https://mcp.airprompter.com/mcp`.
- `skills/airprompter/` tells Claude how to find, run, create, and update your
  saved prompts and workflows.

## What it runs, sends, and fetches

- **MCP server.** Every read, save, and run goes to AirPrompter through the MCP
  server, using the account you signed in with.

## What AirPrompter records when you run a workflow

Every workflow you run through this plugin is reported to AirPrompter and saved
as a run record on your account. This reporting cannot be turned off.

A run record can include:

- which saved workflow ran, when, and from which account, organization, or
  workspace
- the AI tool and connection used, and the plugin version
- the input values you give the run, and any page or file references passed to
  it
- each step's status and timing, and the token counts and model name when Claude
  reports them
- for workflows with scripts on your computer, the outcome and the exit codes of
  scripts that failed

Claude sends each step's output to AirPrompter so the next step can use it. By
default that output is not stored. It is stored only if your account has opted
in to storing run results. Stored output can be read back through AirPrompter
and, if you use workflow evaluation, sent to an AI model that grades it.

AirPrompter also records usage analytics, such as that a run happened and the
workflow's name. Usage totals, such as how many workflows you ran and when you
last connected, go to our email service provider so we can send you product
messages. Your inputs and step outputs are not part of these.

Run records expire after about 120 days. Usage analytics are kept for up to a
year, and summarized totals can be kept longer. AirPrompter runs on Amazon Web
Services. See the [privacy policy](https://airprompter.com/privacy) for more.
