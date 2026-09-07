# v0.3 live runtime checks — 2026-09-07

The official `openai-codex==0.147.0` SDK used the existing managed Codex sign-in.
Model discovery returned the subscription catalog and image-generation capability.
A direct text check returned the requested sentinel. A real image call generated
a red circle; a separate VLM call identified a red circle on white. No API key or
external OAuth token was supplied for these live tests.

`diagram-run.json` and `diagram.jpg` record an upstream planner+critic pipeline,
no-reference mode, one candidate and one critic round. Four unique ephemeral
Codex threads ran Planner → Visualizer → Critic → revised Visualizer, all with
`gpt-5.6-luna` and low effort. Two real image generations occurred. The critic
requested a clearer vector label and a skip connection to the decoder's internal
query input; both appear in the final figure. Independent visual review confirmed
three stages, exactly five passage cards, the original query skip connection,
and no training elements. Initial and revised images are retained separately.
The stopping condition was the requested one-round limit, not a claim that a
second critic approved the revised figure.

`plot-run.json` and `plot.jpg` record a separate upstream plot pipeline with the
same four-stage/thread isolation. Matplotlib code preserved counts A=12, B=19,
C=7, a zero baseline, Count axis label, and exact annotations without fabricated
uncertainty. Generated code ran in a bounded temporary subprocess and exported
300 DPI JPEG. Visual inspection and saved source confirm those invariants. The
critic returned explanatory praise rather than the exact upstream stop sentinel,
so the original exact-match rule performed one fresh code/render revision.

These are qualitative functionality checks on synthetic examples, not benchmark
results or proof of equivalence across providers. External manually supplied
OAuth, Gemini, OpenAI API and Anthropic credentials were not used live. Unit tests
cover configuration priority, isolated requests, SDK request wiring, invalid
critic handling, supplied references and more than three critic rounds. The
native host path's historical evidence remains under the earlier eval directories.
