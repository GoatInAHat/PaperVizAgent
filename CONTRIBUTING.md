# Development

Install Node.js 24, npm, Python 3.11+ and uv. ToolFactory 0.1.2 is pinned by the
Makefile and generated workflows. `uv sync` installs the runtime dependencies.

```sh
make build
make check validate package
```

Build creates generated kernels before MCP introspection, snapshots the real
operations, then regenerates all selected surfaces. Validation runs upstream
host/schema validators and obtains standard shadcn components through its CLI.
Python tests exercise model routing and the reused processor with scripted
backends. Local live tests use the normal signed-in Codex account and are not CI.

## Ownership

Edit `plugin.json` for identity/version, `dev.toolfactory/tool.json` for surfaces,
`src/papervizagent/{config,backends,ops}.py` for runtime behavior, and skill
bodies/reference adapters for native behavior. ToolFactory owns generated
kernels, host adapters, manifests, skill frontmatter, README installation regions
and the lock. Never edit generated regions; adopt first when necessary.
`AGENTS.md` is adopted; CI and release workflows are generated again in v0.3.

Reuse upstream source in `src/papervizagent/upstream`. Keep original prompt
constants unchanged and retain source hashes and modified-file notices. The
standard-library reference helper remains reusable by native hosts. Do not add a
second pipeline engine or a custom OAuth implementation.

For workflow changes, inspect real artifacts and save the source, role IDs,
critic round state, failure/stop reasons and scientific invariants under `evals`.
Do not equate package validation or one live example with benchmark performance.
API-provider tests without real credentials establish request wiring only.

## Releases

Update `plugin.json`, regenerate, run the checks, commit, and push a matching
version tag. The workflow builds artifacts once and publishes configured
registries. [RELEASING.md](RELEASING.md) lists the one-time account setup and
which integrations need manual directory/store submissions.
