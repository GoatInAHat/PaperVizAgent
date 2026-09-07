# Configuration

The tool, command and Python package are now `papervizagent`. Use
`PAPERVIZAGENT_CONFIG` and `PAPERVIZAGENT_DATA_DIR` for its paths.
Provider-specific names such as `CODEX_OAUTH_TOKEN` remain unchanged.

All surfaces use the same optional JSON/YAML file, selected by
`PAPERVIZAGENT_CONFIG`. An absent file setting means native tools in the
skill and managed Codex sign-in in the standalone runtime. No model IDs are
hardcoded into automatic selection.

```yaml
models:
  llm: {provider: codex}
  vlm: {provider: codex}
  image: {provider: codex}
roles:
  critic:
    options: {effort: high}
pipeline:
  task_name: diagram
  exp_mode: demo_full
  retrieval_setting: none
  max_critic_rounds: 3
  num_candidates: 1
  max_concurrent: 4
codex:
  access_token_env: CODEX_OAUTH_TOKEN
  account_id_env: CODEX_ACCOUNT_ID
  timeout: 600
```

This example explicitly assigns all modalities to Codex. To keep the host's
tools as defaults, omit `models` and configure only the roles you want to
override. `status` accepts the native capabilities the host has verified;
`models` reads the actual subscription catalog, including vision eligibility.
Copy an available model ID into any modality or role's `model` field to select
it. An explicit override that fails is an error; it does not silently switch
providers. A role's fields merge over its modality's fields. Native role options are
limited by the host's own controls; `status` exposes common scalar generation
controls and reports other keys as unavailable, without exposing SDK options
or credentials. Use a configured provider for its full SDK option set.

Supported roles: `retriever`, `planner`, `stylist`, `visualizer`, `critic`,
`vanilla`, `polish`. Text-producing roles use `vlm` when their actual inputs
contain images, otherwise `llm`. Render calls use `image`. This includes the two
different modalities used by polish.

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
generator. Image size/aspect/quality/background are requested in the prompt,
not guaranteed API dimensions. Its upstream temperature/token/count defaults
are recorded as unavailable in traces. Explicit unsupported Codex options
fail. Select Gemini or OpenAI image models for their direct API controls.

OpenAI image edits require `options.edit: true` with source image blocks;
polish selects editing automatically. Ordinary Visualizer calls are fresh
generation from the revised text description. Gemini and Codex can condition
on reference image inputs through their native multimodal interfaces.

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
