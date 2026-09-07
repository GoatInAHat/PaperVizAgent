# Development

Consumers install the Codex plugin and use their existing Codex session. The
tools below are only for maintaining and validating this repository.

Install Git, GNU Make, Node.js 24 with npm, Python 3.9+, uv, and zip. Then run:

```sh
make build
make check validate package
```

The Makefile checks out the exact ToolFactory revision in
`dev.toolfactory/source.mk` into the ignored `.cache/toolfactory/` directory and
installs its locked dependencies with pnpm 10.33.0. It uses no model credentials.
`check` detects generated-file drift and runs the standard-library reference-helper tests, `validate` runs the upstream Agent Skills
validator and a real Codex marketplace/install/list cycle in temporary storage,
and the Makefile packages the distributable under `dist/release/`.

The source pin is necessary because this plugin uses the new ToolFactory
`runtime: "none"` mode. It avoids resolving an older npm release that cannot
build this project. ToolFactory's own package command also invokes its npm CLI
internally, so the adopted release path uses a small explicit zip target until
that release is available. Change the pin deliberately and regenerate before
committing.

## Ownership

- `plugin.json`: authored identity, version, description, and licensing.
- `dev.toolfactory/tool.json`: authored surface selection and Codex display data.
- `skills/papervizagent-codex/SKILL.md`: authored body; generated frontmatter and
  operations markers. Do not edit the generated regions.
- `skills/papervizagent-codex/references/`: authored, attributed workflow guidance.
- `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`: generated.
- `README.md`: authored prose; generated installation region.
- `dev.toolfactory/lock.json`: generated ownership and drift ledger.

`AGENTS.md`, `.github/workflows/ci.yml`, and `.github/workflows/release.yml` were
explicitly adopted with ToolFactory's `adopt` command. They provide concise
project guidance, source-pinned CI, and a GitHub-only release with no registry
credentials. Other generated agent-configuration files retain ToolFactory's
template ownership. Running `.agents/setup` is optional developer integration;
it is not part of consumer installation.

The reference helper is the only installed Python helper; it uses the standard
library and performs no model inference. Vendored prompts/guides are checked by
hash against UPSTREAM.json; native adapters carry deliberate behavior changes.

## Behavior changes

Use the cases in [evals/cases.json](evals/cases.json). Run relevant cases in a
fresh Codex task with the candidate skill loaded. Inspect actual outputs and
record the host tool, call count, scientific invariants, and defects. Live image
tests consume the signed-in account's included usage, so they are intentional
manual evaluations rather than CI jobs. Keep automated structural checks and
observed model behavior separate.

Preserve the upstream Apache-2.0 license, NOTICE, and exact attribution in
UPSTREAM.json when adapting additional official guidance. Do not import paper
figures, datasets, or examples without checking their own licensing.

## Release

Update the version in `plugin.json`, run `make build check validate package`,
commit, and push a matching `vX.Y.Z` tag. The release workflow verifies the tag,
reruns validation, and publishes the plugin archive to GitHub.
It does not publish an npm package or submit to a curated plugin directory.
