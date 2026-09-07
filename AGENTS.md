# PaperVizAgent for Codex

This is a native Codex instruction plugin. Keep planning, generation, and review
in the active host session. Do not add an inference client, OAuth-token reader,
provider configuration, MCP server, or local model runtime.

The skill body and its references are authored sources. ToolFactory generates
the plugin manifest, marketplace entry, skill frontmatter, and install section.
Edit `plugin.json` and `dev.toolfactory/tool.json`, then run `make build`.
Never hand-edit generated paths in `dev.toolfactory/lock.json`; use ToolFactory
`adopt` before taking ownership. The adopted CI/release workflows and this file
are intentional; see CONTRIBUTING.md.

Run `make check validate package` after metadata or packaging changes. Behavioral
cases are in `evals/cases.json`; use a fresh Codex task for material skill changes
and inspect the actual output. Preserve sources, exact prompts, candidates, and
an honest visual review. Never claim a live evaluation ran when it did not.

Keep upstream provenance and Apache-2.0 attribution intact. Preserve scientific
labels and connections during stylistic changes. Do not treat images as
editable vectors or infer measurements from paper prose.
