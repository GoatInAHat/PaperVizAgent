# PaperVizAgent

Reuse the pinned upstream Python processor and role implementations. Keep role prompts and complete style guides unchanged; document adapter changes and source hashes. Each host-native role must have a fresh subagent context; each runtime role must use a fresh provider request or ephemeral Codex thread with bounded inputs and real artifact handoffs.

Model routing is explicit role override, modality override, verified host-native capability, then Codex for missing capabilities. Never infer capability from a host name. Use official provider SDKs; do not add a custom OAuth client or read an unrelated application's credentials. Caller-supplied tokens belong in host secret settings, environment variables or an explicitly selected file, never prompts or traces.

ToolFactory owns generated metadata, kernels, surface adapters, skill frontmatter and README installation regions. Edit plugin.json, dev.toolfactory/tool.json and authored source, then run make build. Never hand-edit generated regions or lock.json; adopt a file before taking ownership. This file is deliberately adopted. The public Python runtime lives in src/papervizagent_codex; the npm package is only a launcher.

Run make check validate package. Material workflow changes require live text/vision/image and pipeline checks, actual artifact inspection, role/thread IDs, critic state and stop conditions. Unit tests and packaging checks do not establish benchmark equivalence. API-only provider paths need explicit integration evidence before claiming a live pass.

Preserve attribution, exact scientific data and meaningful legends. Plot subprocesses bound execution time and isolate global state; they are not a security sandbox. Avoid another workflow framework, persistence layer, auth implementation or provider class per role: upstream and the official SDKs already supply the needed work.
