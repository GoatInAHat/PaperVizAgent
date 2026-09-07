# Native full-mode smoke run

The requested two-call run produced both initial images and completed one independent visual Critic review. It stopped with `budget_exhausted`, not acceptance. The selected image is `figure-stylist.png` (1755 × 896); the earlier `figure-planner.png` (1774 × 887) is retained as the full-mode evolution artifact.

## Execution

- Mode: full; one candidate.
- Retrieval: explicit none; no reference network retrieval or invented examples. Retriever invocation was skipped intentionally.
- Image calls: exactly 2 native calls, both successful; zero retries, edits, or critic-driven regenerations.
- Critic rounds: round 0 completed with valid two-field JSON and a complete revised description. Rounds 1 and 2 were skipped after the budget stop.
- Native context isolation: `fork_turns:none` on all five invocations; one active role worker at a time. Each Visualizer used imagegen directly; no coordinator tool bridge.
- No external model process, provider setup, API credentials, public mutations, or plugin-source edits were used. Intentional run files are confined to this run; native imagegen also saved its automatic host originals, which were copied unchanged here.

| Role | Returned native agent ID | Result |
|---|---|---|
| Planner | /root/native_pipeline_smoke/planner | Complete description saved |
| Stylist | /root/native_pipeline_smoke/stylist | Complete styled description saved |
| Visualizer: Planner | /root/native_pipeline_smoke/visualizer_planner | One call; PNG saved and inspected |
| Visualizer: Stylist | /root/native_pipeline_smoke/visualizer_stylist | One call; PNG saved and inspected |
| Critic: round 0 | /root/native_pipeline_smoke/critic_0 | Actual styled PNG inspected; revision required |

## Scientific inspection

The coordinator inspected both full saved PNGs through native `view_image`. The selected styled image preserves the source requirements: a user question feeds the frozen question encoder; the query vector feeds the nearest-neighbor retriever; a read-only document index feeds that retriever; exactly five cards P1–P5 are grouped into the generator; the original question separately bypasses directly to the generator; and the answer contains illustrative passage citations. No training, reranking, web-search, verification, index-update, or feedback stage appears. Both meaningful frozen/read-only legend entries remain. No scientific regression from Planner to Stylist was observed, so no rollback was applied.

The independent Critic likewise found the scientific workflow faithful. Its requested change is to remove the full caption sentence embedded along the bottom of the image and keep that caption external. `critic-0.json` preserves the exact review, and `critic-description-0.md` preserves its complete revised description. That revision has not been rendered or accepted.

## Unresolved output and workflow defects

1. The selected image embeds the supplied caption. The independent Critic requested its removal; this remains unresolved at the image-call limit.
2. Both images include “Inference workflow” despite the exact Visualizer prompt's final instruction to omit figure titles. The Planner description permitted this title, the Stylist required it, and the Critic's revision explicitly preserves it. This is a real cross-role instruction conflict exposed by the test. The revised description remains unchanged as evidence and would still conflict with the standard Visualizer wrapper on resume.
3. In the selected styled image, “Indexed passages” interrupts the vertical index-to-retriever connector instead of sitting alongside it. The arrow direction remains interpretable. This was observed by the Visualizer and coordinator but was not raised by the Critic.
4. The earlier Planner image has small gaps between passage-card borders and the collection connector. This was not a reason to select it over the styled image.

The first Visualizer reported that its local native image viewer showed an upper-left crop, while its generation preview showed the full image. The coordinator's local native viewer displayed the complete identical saved PNG, so that viewer limitation was not reproduced. All PNGs were validated by signature, dimensions, SHA-256, and byte-identical source copies. Exact prompts were verified against the complete original Visualizer role prompt plus the complete corresponding description and required final instruction.

## Resume

The saved next stage is `render_critic_0`. It requires additional explicitly authorized image budget and a fresh Visualizer invocation. Preserve the selected styled image/description pair until a new render actually exists. The title conflict should be resolved explicitly in the resumed text; do not claim that the saved Critic revision already fixes it. This run does not demonstrate auto-reference retrieval, critic regeneration, multiple candidates, editable SVG, plotting, or benchmark quality. It is a budget-limited full-mode run, and publication readiness is not claimed.
