# PaperVizAgent for Codex

Scientific figures through separate native Codex agents, using the session
you're already signed into. No API keys, model configuration, MCP server, or GPU setup.

An independent port of [Google Research's PaperVizAgent](https://github.com/google-research/papervizagent)
(formerly PaperBanana), built with [ToolFactory](https://github.com/GoatInAHat/toolfactory).
It preserves the original role prompts, complete style guides, reference-driven
planning, and critic/regeneration loop. This is not an official Google or
OpenAI integration.

<!-- tf:install -->
## Install

[![Agent Skill](https://img.shields.io/badge/Agent_Skill-available-5B5BD6)](https://github.com/GoatInAHat/PaperVizAgent-codex)

- **Agent Skill** — `npx skills add GoatInAHat/PaperVizAgent-codex`
- **MCP server** — `uvx papervizagent-codex mcp` [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=papervizagent-codex&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22papervizagent-codex%22%2C%22mcp%22%5D%7D) [![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=papervizagent-codex&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJwYXBlcnZpemFnZW50LWNvZGV4IiwibWNwIl19)
- **Claude Desktop extension** — download `papervizagent-codex.mcpb` from the GitHub Release and double-click to install
- **Claude Code plugin** — `claude plugin marketplace add GoatInAHat/PaperVizAgent-codex`, then `claude plugin install papervizagent-codex@papervizagent-codex`
- **Codex plugin** — `codex plugin marketplace add GoatInAHat/PaperVizAgent-codex`, then `codex plugin add papervizagent-codex@papervizagent-codex`
- **Gemini CLI extension** — `gemini extensions install https://github.com/GoatInAHat/PaperVizAgent-codex`
- **OpenClaw plugin** — `openclaw plugins install --link hosts/openclaw` from a checkout; published: `openclaw plugins install clawhub:openclaw-plugin-papervizagent-codex`
- **Hermes plugin** — `hermes plugins install https://github.com/GoatInAHat/PaperVizAgent-codex#hosts/hermes/papervizagent_codex_hermes`
- **DSH plugin** (experimental) — `dsh plugin --profile <profile> add ./hosts/dsh` from a checkout, or the release tarball `papervizagent-codex-dsh-0.3.0.tgz`
- **Browser extension** — from a checkout: `npm --prefix hosts/browser install && npm --prefix hosts/browser exec --no -- wxt build`,
  then `chrome://extensions` → developer mode → Load unpacked → `hosts/browser/.output/chrome-mv3`
  (Firefox: `npm --prefix hosts/browser exec --no -- web-ext run`). Each GitHub Release attaches the
  store uploads `papervizagent-codex-0.3.0-chrome.zip`, `papervizagent-codex-0.3.0-firefox.zip`, `papervizagent-codex-0.3.0-edge.zip`, and the Mozilla-signed `.xpi`,
  which is the only download-and-install channel now that Chrome no longer keeps side-loaded unpacked
  extensions; the Chrome Web Store, Firefox Add-ons and Edge Add-ons listings appear once the release's
  submit step has each store's credentials. Then pair it: `uvx papervizagent-codex mcp --http --pair`
  prints the `<url>#<token>` the extension's options page accepts.
- **Web app** — `uvx papervizagent-codex mcp --http --open` serves the operations page beside the
  MCP endpoint on one port and opens it; over MCP or a skill, the `web` operation does the same and
  returns the URL.
- **npm package** — `npm install papervizagent-codex`; requires `uv`, and `papervizagent-codex` delegates to `uvx --from papervizagent-codex==0.3.0 papervizagent-codex`
- **PyPI package** — `uv add papervizagent-codex`

<!-- /tf:install -->

After installation, start a new Codex task:

```text
Use $papervizagent-codex to turn this paper's methods section into a scientific
diagram. Use this caption: "Overview of our inference pipeline."
```

Attach the paper or paste the relevant source. The default workflow uses full
mode, automatic reference retrieval, one candidate, and three critic rounds.
You can request a different mode, a smaller image budget, supplied references,
or no retrieval in ordinary language.

## Actual separate agents

The main Codex agent coordinates files and state. Each role receives a fresh
native context with its original prompt and explicit inputs.

| Role | Input and behavior |
|---|---|
| Retriever | Ranks the real reference pool using target methods/data and caption; retrieves up to ten source/caption/image examples |
| Planner | Inspects those examples and writes a complete target description |
| Stylist | Refines the planner description using the complete task-specific style guide |
| Visualizer | Renders the description through native image generation, or executable Matplotlib code for plots |
| Critic | Independently inspects the current image against its description and raw source; returns a critique and complete revised description |

The Critic's revised description produces a **new image from text**. Editing an
existing bitmap is a separate user-requested workflow. Every critic round uses a
fresh context; no headings or role-play substitute for actual delegation.

Full mode retains both planner and styled initial renders. With up to three
critic-driven regenerations, that is at most five visible image-tool calls per
candidate, with early stopping. A smaller requested budget is respected and
recorded as a partial run when it prevents a stage. Failed visible calls count
against the budget; there are no automatic retries. Subagents and reference
processing also consume the signed-in account's usage.

The available modes are full, planner_critic, planner_stylist, planner, vanilla,
retriever, and polish. Explicit editable SVG is an additional renderer.
[Workflow details](skills/papervizagent-codex/references/workflow.md) document
their role graphs and stopping rules.

## Reference retrieval without setup

The plugin fetches pinned metadata and only selected images from the original
author's public PaperBanana Space. It does not download the entire dataset
archive or bundle third-party paper figures.

A Python 3.9+ standard-library helper handles downloads, caching, checksums and
materialization; Codex performs the ranking. No Python packages or inference
credentials are needed for retrieval. The complete first-200 diagram candidate
pool is processed in batches rather than silently truncating source methods.
The Planner receives the selected complete methods/data, captions and actual
images. See [retrieval provenance](skills/papervizagent-codex/references/retrieval.md).

When network/reference access is unavailable, the run explicitly records
no-reference operation. Supplied references and an explicit no-retrieval request
also work. Manual/random benchmark ablations are not implemented by the helper.

## Host requirements and artifacts

Use a current signed-in Codex session with native subagents, image generation,
visual inspection, and file access. Native agent configuration is inherited;
the plugin does not write custom-agent files or read OAuth tokens.
[Official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)

The host's image tool chooses its available model and supported dimensions.
Image usage is subject to the account's included limits.
[Official image-generation documentation](https://learn.chatgpt.com/docs/image-generation)

The reference helper uses available host Python; native fetch tools can provide
the same data if Python is absent. Data plots use the host's available
Python/Matplotlib runtime, preserving source and raw data. A missing capability
is reported explicitly; no alternate model provider is launched.

A run saves source/caption, retrieval provenance, separate descriptions, exact
prompts, all real outputs, structured critic results, and run.json with role IDs,
rounds, failures, selected output, and stop reason. Figures go to the requested
directory or a new directory under outputs/figures/, respecting host rules.
Raster output remains raster; requested SVG uses native editable elements.

## Fidelity and validation

v0.1.0 collapsed roles into one context and changed several core behaviors.
v0.2 restores separate contexts, real retrieval, full prompts/guides, pipeline
modes, separate evolution artifacts, the original three-round critic contract,
and task-specific plotting.

[FIDELITY.md](FIDELITY.md) records the audit, exact source evidence, and remaining
adaptations: native models/transport, one conversational candidate, batched
retrieval, caption inference when absent, preserved meaningful legends, and an
additional SVG renderer. The original demo's ten-candidate planner+critic default
is not silently described as this plugin's default.

The port does not inherit the paper's benchmark results. The qualitative Critic
is distinct from the original ground-truth evaluation. Review scientific
content and venue requirements before treating any output as final.
[Evaluation cases and observed results](evals/README.md)

## Example

![Previously tested scientific workflow](examples/retrieval/figure-v2.png)

This example is retained from the v0.1 native rendering/edit test. It demonstrates
image output, not evidence of the new role orchestration. The
[synthetic source](examples/method.md), [original image](examples/retrieval/figure-v1.png),
[edit prompt](examples/retrieval/prompt-v2.md), and
[visual review](examples/retrieval/review.md) are available for inspection.
Current native-role tests are recorded separately under evals/.

## Development

ToolFactory owns the manifest, marketplace entry, skill metadata and installation
projections. The skill's coordinator instructions, native-role adapters, and
standard-library reference helper are authored here. See
[CONTRIBUTING.md](CONTRIBUTING.md) for regeneration and validation.

[UPSTREAM.json](UPSTREAM.json) records exact source, prompt, guide and metadata
hashes. [NOTICE](NOTICE) describes attribution and modifications. Code is
licensed under [Apache-2.0](LICENSE); downloaded reference figures retain their
source provenance and are not redistributed by this plugin.

<!-- tf:mcp-name -->
<!-- mcp-name: io.github.GoatInAHat/papervizagent-codex -->
<!-- /tf:mcp-name -->
