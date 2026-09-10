# Configuration

The tool, command and Python package are now `papervizagent`. Use
`PAPERVIZAGENT_CONFIG` and `PAPERVIZAGENT_DATA_DIR` for its paths.
Provider-specific names such as `CODEX_OAUTH_TOKEN` remain unchanged.

All surfaces use the same optional JSON/YAML file, selected by
`PAPERVIZAGENT_CONFIG`. An absent file setting means native tools in the
skill and managed Codex sign-in in the standalone runtime. No model IDs are
hardcoded into automatic selection.

```yaml
model_policy: balanced
pipeline:
  task_name: diagram
  exp_mode: demo_full
  retrieval_setting: none
  max_critic_rounds: 3
  num_candidates: 1
  max_concurrent: 4
```

This example preserves verified host-native tools, with managed Codex sign-in
for missing modalities. `status` accepts the native capabilities the host has
verified. `models` reads the actual subscription catalog and reports automatic
choices and selection reasons without making an inference request.

`model_policy` is `balanced` by default; choose `quality` for highest-quality
work. The `status`, `infer`, and `generate` operations also accept a per-request
`model_policy` override. Native skill roles use a supported current mid-tier
alias or live catalog; Claude Code uses `sonnet`, or `opus` for quality. Hosts
without tier information use their own default and record the fallback.

The Codex runtime discovers models at connection time. Automatic selection
excludes hidden and specialized entries, requires vision support for image
inputs, and prefers entries without retirement/upgrade hints. It uses the
provider's balanced/mid-tier or flagship/most-capable descriptions, then the
provider default, then catalog order. These advisory labels cannot guarantee
lowest cost or benchmark ranking. Model IDs and version numbers are never
hardcoded or guessed. Selection reasons are recorded in traces, so a changed
catalog remains inspectable. Balanced effort is medium for text/vision and low
for the image-tool coordinator where supported; quality prefers high effort.

Copy an available model ID into a modality or role's `model` field to override
automatic selection. Set `provider` to explicitly override native-first routing.
For example, `models.image: {provider: codex, model: YOUR_AVAILABLE_MODEL}` pins
the Codex coordinator while leaving native text and vision available. An
explicit override that fails is an error; it does not silently switch providers
or models. A role's fields merge over its modality's fields. Explicit effort
options also win over the policy defaults.

Native role options are limited by the host's own controls; `status` exposes
common scalar generation controls and reports other keys as unavailable,
without exposing SDK options or credentials. Use a configured provider for its
full SDK option set.

Supported roles: `retriever`, `planner`, `stylist`, `visualizer`, `critic`,
`vanilla`, `polish`. Text-producing roles use `vlm` when their actual inputs
contain images, otherwise `llm`. Render calls use `image`. This includes the two
different modalities used by polish.

## Native Python callbacks in 0.5.0

Version 0.5.0 extends the embedded `Backend(native={...})` callback contract.
Callbacks with an explicit signature must add the keyword arguments `model`
and `model_policy` alongside `role`, `modality`, `system`, `contents`, and
`options`. `model` is `None` when unconfigured; otherwise apply that exact
model. When it is absent, resolve `model_policy` through the host's supported
aliases/catalog. Preserve explicit controls in `options`. Returning a result
without applying an explicit model is not a valid native adapter.

This is a breaking change for callbacks with the old five-argument signature;
update the adapter before upgrading. Skills and generated CLI/MCP/host adapters
already share the updated policy and do not need callback code.

## Providers

Each model/role entry accepts `provider`, `model`, `api_key_env`, `api_key`,
`base_url`, `vertexai`, `project`, `location`, and `options`.

| Provider | Text/vision | Image | Authentication and options |
|---|---|---|---|
| `native` | Host-dependent | Host-dependent | Skill or supplied Python callbacks; no SDK call |
| `codex` | Discovered catalog | Built-in tool if available | Existing sign-in or external OAuth; `effort`, `service_tier`, `output_schema` |
| `gemini` | Gemini generate-content API | Image-capable Gemini models | `GOOGLE_API_KEY`/`GEMINI_API_KEY`, or Vertex ADC/project/location; SDK generation options |
| `openai` | Chat Completions, including compatible endpoints | Images API | `OPENAI_API_KEY` or custom `api_key_env`; SDK request options |
| `anthropic` | Messages API | Unavailable | `ANTHROPIC_API_KEY`, or `vertexai: true`; SDK request options |

Provider SDKs are bundled as dependencies and initialized only when used.
Standard environment keys take precedence over inline `api_key`; environment
or the host's secret UI is preferable to storing a key in a file. Keep private
configuration out of git. OpenAI-compatible endpoints can use a custom
`base_url`, model, and key variable. Unsupported endpoint options produce the
provider's error rather than silently disappearing.

For example, assign only image rendering to Gemini while keeping native text
and vision defaults:

```yaml
models:
  image:
    provider: gemini
    model: YOUR_IMAGE_CAPABLE_GEMINI_MODEL
    api_key_env: GOOGLE_API_KEY
    options:
      image_config: {aspect_ratio: '16:9', image_size: '2K'}
```

The unmodified upstream `model_config.yaml` shape (`defaults`, `api_keys`,
`google_cloud`, `anthropic`) is accepted. Its default model names choose the
same Gemini path and `gpt-image` image path as upstream. Portable `models`,
`roles`, `codex`, and `pipeline` sections can extend it; portable model entries
take precedence. Select Anthropic explicitly to use its text adapter.

Codex image `model` selects the coordinator, not the service-managed image
generator. The subscription interface does not expose or report its underlying
image-model ID, so it cannot guarantee a `gpt-image-2` pin. Existing Codex login
is reused through the official SDK without copying OAuth credentials.
Image size/aspect/quality/background are requested in the prompt,
not guaranteed API dimensions. Its upstream temperature/token/count defaults
are recorded as unavailable in traces. Explicit unsupported Codex options
fail. Select Gemini or OpenAI image models for their direct API controls.

OpenAI image edits require `options.edit: true` with source image blocks;
polish selects editing automatically. Ordinary Visualizer calls are fresh
generation from the revised text description. Gemini and Codex can condition
on reference image inputs through their native multimodal interfaces.

## Claude Code with existing Codex sign-in

Install the shared skill and an MCP server. While PyPI publication is pending,
use Git source for the runtime too; the generated marketplace plugin's PyPI
command requires that publication. These commands install the current main
branch; replace `main` with a reviewed commit for a reproducible installation.

```sh
npx skills add GoatInAHat/PaperVizAgent --skill papervizagent --agent claude-code --global --yes
claude mcp add --scope user papervizagent -- uvx --from git+https://github.com/GoatInAHat/PaperVizAgent@main papervizagent mcp
claude --model sonnet
```

Claude and Codex each use their own existing login (`claude auth login` and
`codex login` if needed). Do not move Codex OAuth tokens into Claude. Ask Claude
to use the PaperVizAgent skill: fresh Claude roles plan and inspect images;
`infer` invokes the Codex image bridge only when that modality is absent.
The Codex image bridge necessarily includes a small coordinating LLM request,
with low effort under the balanced policy; it is not a direct image-only API.

For an unattended demonstration, constrain built-in tools with `--tools` and
use `--strict-mcp-config` with an explicit server file. Allow Read, Write, Agent
and the needed MCP operations; omit scheduler/polling tools. Resume on Claude's
automatic role-completion notifications. Record the resolved model metadata,
actual artifact inspection and any failed stages rather than assuming a host
integration implies success.

## External Codex tokens

Supply `CODEX_OAUTH_TOKEN` through the host's secret field or environment. An
explicit `CODEX_ACCOUNT_ID` overrides a JWT's account claim. Alternatively:

```yaml
codex:
  token_file: ./private/codex-token.json
```

The selected file contains `accessToken` and, when needed, `chatgptAccountId`.
Relative token paths resolve against the configuration file. The adapter passes
them to the official app-server `chatgptAuthTokens` login API, in memory. It
does not extract tokens from another app or implement OAuth refresh. Replace
an expired token before the next operation. For automatic refresh, use the
SDK's managed Codex sign-in. `codex.codex_bin` optionally selects an installed
CLI; otherwise the official SDK's bundled CLI is used. `codex.config` passes
documented thread configuration to that runtime.

## Pipeline and data

`generate.data` preserves upstream's dictionary format. Common fields are
`content`, `visual_intent`, `additional_info.rounded_ratio`, `retrieved_examples`,
`top10_references`, `max_critic_rounds`, and `path_to_gt_image` for polish.

`generate.settings` overrides the file's `pipeline` section. Supported settings:
`work_dir`, `dataset_name`, `task_name` (`diagram`/`plot`), `split_name`,
`exp_mode`, `retrieval_setting`, `temperature`, `max_critic_rounds`, `timestamp`,
`plot_timeout_seconds` (30), and `plot_dpi` (300). `num_candidates` and
`max_concurrent` can be set in the pipeline section or operation arguments.
Upstream evaluation requires its separate benchmark environment; this runtime
does not claim benchmark evaluation support.

Modes: `vanilla`, `dev_planner`, `dev_planner_stylist`, `dev_planner_critic`,
`demo_planner_critic`, `dev_full`, `demo_full`, `dev_retriever`, `dev_polish`.
Retrieval: `auto`, `manual`, `random`, `none`. For dataset retrieval, put the
upstream `ref.json` and images under
`<work_dir>/data/PaperBananaBench/<task_name>/`. Supplied `retrieved_examples`
also work with `none`; use the existing skill's reference helper to materialize
selected public examples without downloading the dataset archive. Custom style
guides at `<work_dir>/style_guides/neurips2025_<task_name>_style_guide.md` take
precedence over the bundled guides.

Polish accepts an absolute `path_to_gt_image`, or a path relative to the dataset
task directory. Retrieval-only returns results without an image. Missing final
images in other modes are errors. Figures and the upstream result dictionary
are saved separately from the credential-free role trace. Native skill runs
retain the host's own artifact and sandbox conventions.
