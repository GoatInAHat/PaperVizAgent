# PaperVizAgent for Codex

This is a native Codex port of the official PaperVizAgent role pipeline.
Runtime use requires fresh native subagents, bounded role inputs, and real
artifact handoffs. Do not collapse roles into a single conversation or add
an inference client, OAuth-token reader, provider configuration, or MCP server.
The standard-library reference helper fetches public data; it performs no
inference. Native host/dependency tools provide plotting and rendering support.

ToolFactory generates plugin/marketplace metadata, skill frontmatter, and the
README install region. Edit plugin.json and dev.toolfactory/tool.json, then
run make build. Never hand-edit generated regions or lock.json; use ToolFactory
adopt before taking ownership. CI/release and this file are deliberately adopted.

Run make check validate package after changes. Material workflow changes also
need independent live tests using evals/cases.json and actual artifact inspection.
Record role IDs, isolation, critic round state, image calls and stop reasons.
Do not claim live evaluation or benchmark equivalence from package validation.

Original role prompts and style guides are vendored with provenance in
UPSTREAM.json. Keep their wording intact; native adapters and deliberate
differences belong in references/compatibility.md and FIDELITY.md.
Preserve upstream attribution, user science, exact data and meaningful legends.
