# PaperVizAgent

Scientific figures using [Google Research’s official PaperVizAgent](https://github.com/google-research/papervizagent) pipeline, with separate roles and configurable inference on every surface. This independent distribution keeps its original repository/package name, `papervizagent-codex`.

The Python processor, seven agent implementations and complete style guides are reused from pinned upstream source. [ToolFactory](https://github.com/GoatInAHat/toolfactory) generates the integrations and release packages from that one runtime.

**Release status:** GitHub/source installation is available; the PyPI, npm, ClawHub and browser-store commands below require the publisher setup described in [RELEASING.md](RELEASING.md). Until PyPI is published, run the runtime from the release source:

```sh
uvx --from git+https://github.com/GoatInAHat/PaperVizAgent-codex@v0.3.0 papervizagent-codex mcp
```

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
  store uploads `papervizagent-codex-0.3.0-chrome.zip`, `papervizagent-codex-0.3.0-firefox.zip`, `papervizagent-codex-0.3.0-edge.zip`. When Firefox signing credentials are configured, it also attaches a
  Mozilla-signed `.xpi`; the Chrome Web Store, Firefox Add-ons and Edge Add-ons listings appear once the release's
  submit step has each store's credentials. Then pair it: `uvx papervizagent-codex mcp --http --pair`
  prints the `<url>#<token>` the extension's options page accepts.
- **Web app** — `uvx papervizagent-codex mcp --http --open` serves the operations page beside the
  MCP endpoint on one port and opens it; over MCP or a skill, the `web` operation does the same and
  returns the URL.
- **npm package** — `npm install papervizagent-codex`; requires `uv`, and `papervizagent-codex` delegates to `uvx --from papervizagent-codex==0.3.0 papervizagent-codex`
- **PyPI package** — `uv add papervizagent-codex`

<!-- /tf:install -->

The npm package is a small launcher for the same version on PyPI and requires [uv](https://docs.astral.sh/uv/getting-started/installation/). MCPB uses its host’s supported uv runtime. Downloadable bundles and registry listings are separate: see [release status](RELEASING.md).

## Defaults and model choice

The skill resolves each role independently: **explicit role setting → modality setting → available host tool → Codex fallback**. It checks actual tools; a host name does not guarantee vision or image generation.

On Codex, the skill uses native subagents, vision and image generation without API keys or a Python server. The Codex plugin does not eagerly start MCP. Custom overrides use the optional runtime through the CLI or an explicitly connected MCP server.

On other hosts, use available native capabilities and supply `CODEX_OAUTH_TOKEN` for missing capabilities, or use an existing Codex sign-in. `CODEX_ACCOUNT_ID` is needed only if the supplied token does not contain its account identifier. Tokens stay in environment/host secret settings or an explicitly selected token file; never paste them into prompts or tool arguments. Static access tokens expire: their owner must refresh them. The SDK manages refresh for its own sign-in.

A standalone CLI/MCP/web server cannot directly invoke another app’s private tools. Its `generate` operation uses configured SDK providers or Codex. The portable skill is the bridge to host-native tools; embedded Python integrations can also supply native callbacks to `Backend(native={...})`. An unavailable capability produces an error.

The official [Codex SDK](https://github.com/openai/codex/tree/main/sdk/python) discovers subscription models and starts a fresh, ephemeral thread for every role call. `models.image.model` selects the Codex **coordinating model**; Codex manages the built-in image generator. Arbitrary image-model selection uses an image API provider. Codex does not expose API controls such as temperature or maximum output tokens; explicit unsupported overrides fail, and unavailable upstream defaults are listed in the trace. Aspect/size requests are prompt guidance on Codex. See [configuration](CONFIGURATION.md).

## Use

In an agent host:

```text
Use $papervizagent-codex to turn these methods and this caption into a scientific diagram.
```

With the runtime installed:

```sh
papervizagent-codex status --json '{"native":["llm","vlm"]}'
papervizagent-codex models
papervizagent-codex generate --json '{"data":{"content":"Encode the input, retrieve evidence, then decode the answer.","visual_intent":"Overview of the inference pipeline"},"settings":{"exp_mode":"demo_full","retrieval_setting":"none","max_critic_rounds":3}}'
papervizagent-codex mcp
```

`status` only resolves configuration. `models` verifies the Codex account catalog without inference. `infer` runs one isolated role and returns text or an image path plus its trace. `generate` runs the upstream pipeline, retaining intermediate descriptions, code, image data and role traces under the tool’s data directory. Set `PAPERVIZAGENT_CODEX_DATA_DIR` to choose it.

Both diagrams and Matplotlib plots support vanilla, planner, planner+stylist, planner+critic, full, retrieval-only and polish modes. Candidate count, concurrency, critic rounds, retrieval mode, aspect ratio, style guides and provider options remain configurable. The skill defaults to automatic reference retrieval; the standalone runtime defaults to `none` until a reference dataset or supplied examples are provided. The runtime defaults to one full candidate and three critic rounds; upstream’s ten-candidate demo is a selectable configuration, not an implied default.

Original prompt constants and style guides remain unchanged. Each native role has a fresh subagent; each runtime role makes an isolated provider request or Codex thread. Critic revisions produce fresh renders; polish is a separate editing workflow. Plot execution runs generated Python in a temporary child process with a configurable timeout and 300 DPI output. This isolates plotting state and hangs; it is **not an OS security sandbox**. Use the host’s execution sandbox for untrusted inputs.

## Development and fidelity

```sh
uv sync
make build
make check
make validate
make package
```

[FIDELITY.md](FIDELITY.md) records historical gaps and current adaptations. [UPSTREAM.json](UPSTREAM.json) and the runtime’s own provenance manifest pin reused source. [Configuration](CONFIGURATION.md) documents provider and pipeline settings. [Release status](RELEASING.md) distinguishes packaged integrations from published listings. This port does not inherit upstream’s benchmark scores and is not an official Google or OpenAI integration.

<!-- tf:mcp-name -->
<!-- mcp-name: io.github.GoatInAHat/papervizagent-codex -->
<!-- /tf:mcp-name -->
