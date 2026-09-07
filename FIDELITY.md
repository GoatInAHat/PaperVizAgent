# Fidelity audit and v0.2 restoration

The v0.1 plugin was a prompt/workflow adaptation, not a faithful execution of
the original agent architecture. Its native image smoke tests did not test role
isolation, retrieval, or critic-loop equivalence. That gap was an implementation
decision, not a limitation of Codex sign-in.

This audit compares v0.1.0 with the official implementation at
[e088a8fff74cc363b6897c0843631fff76484908](https://github.com/google-research/papervizagent/tree/e088a8fff74cc363b6897c0843631fff76484908).
The original agents are separate role-specific model calls and Python objects,
orchestrated in one Python process. They are not separate operating-system
processes. Native Codex subagents preserve the relevant context separation.

## Material departures found

| Behavior | v0.1.0 | v0.2 implementation |
|---|---|---|
| Role separation | All reasoning and self-review in one conversation | Fresh native role contexts with explicit inputs, outputs, agent IDs, and per-round Critic contexts |
| Reference-driven planning | Replaced reference retrieval with supplied images or generic layout heuristics | Native Retriever ranks the real first 200 diagram references or all plot references; Planner receives full source/caption/image pairs |
| Role prompts and styling | Condensed prompts and custom style defaults | All 16 original prompt constants plus both complete synthesized guides, with documented native-tool adapters |
| Critic refinement | Targeted edits to the prior bitmap | Strict critique + complete revised description → fresh generation; explicit user edits remain a separate path |
| Iterations and stop state | Two correction passes; prose review | Three critic rounds; structured results, stop reason, round state, saved render failures, budget tracking |
| Evolution and modes | Always Stylist; one initial image | Full/planner+critic/planner+stylist/planner/direct/retrieval/polish graphs; full retains both planner and styled initial renders |
| Statistical plots | Generic plotting guidance | Original plot-specific roles, Matplotlib source, exact data mapping and missing-render failure critique |
| Evaluation coverage | One generation and one user edit | Adds independent-role execution, retrieval helper tests, critic correction, actual run records and failure/budget observations |

Source evidence:

- [Agent construction](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/main.py#L106)
  and [pipeline/critic state](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/utils/paperviz_processor.py#L60).
- [Full-content retrieval](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/agents/retriever_agent.py#L141)
  and [multimodal Planner input](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/agents/planner_agent.py#L64).
- [Complete guide input](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/agents/stylist_agent.py#L60)
  and [Critic's required image/description/source](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/agents/critic_agent.py#L69).
- [Both initial renders and text-only regeneration](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/agents/visualizer_agent.py#L114).
- [Demo defaults](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/demo.py#L382)
  and [three-round configuration](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/utils/config.py#L31).

The live v0.2 test also found a cross-role caption/title conflict: Planner and
Stylist could request a title that the Visualizer wrapper excluded, while Critic
preserved it. The shared native adapter now applies the same placement rule to
all roles and checks descriptions at handoff, with one recorded text repair
before any further rendering. The original smoke artifacts retain this failure
as evidence rather than being overwritten.

## Remaining differences are explicit

1. **Runtime/models:** native Codex inference and tools replace provider SDKs.
   Codex follows the orchestration skill and invokes native agents; the
   original Python processor is not running. Model sampling, supported image
   size, JPEG conversion, and the paper's
   quality scores cannot be reproduced exactly by swapping models.
2. **Defaults:** one full-pipeline candidate is the conversational default.
   The original demo defaults to ten planner+critic candidates at 21:9; this
   is not a universal algorithm default. User requests can override the mode,
   candidate count, aspect ratio, rounds, and call budget without a config file.
3. **Retrieval context:** read every candidate's complete content in batches
   and retain ranked shortlists because the first-200 diagram pool is about
   3.19 MB. This differs from the original single huge retrieval prompt. The
   original author's pinned public Space supplies per-file metadata and selected
   images; both metadata files were verified byte-for-byte against the official
   dataset ZIP, including record order. No full dataset archive or third-party
   figure corpus ships here.
   Supplied references and none are supported; original manual/random benchmark
   ablations are not reproduced by the fetch helper.
4. **Scientific safeguards:** keep meaningful legends despite the original
   broad legend-removal instruction, and allow a recorded semantic-regression
   rollback. Original selection otherwise takes the latest valid render.
5. **Convenience extensions:** an omitted caption may be proposed and labeled
   as inferred; the original demo requires a caption. Native editable SVG is
   additional functionality, not an upstream vectorization system.
6. **Product/evaluation scope:** no Streamlit grid, batch-export UI, benchmark
   runner, or claimed original scores. The qualitative Critic is distinct from
   [ground-truth benchmark evaluation](https://github.com/google-research/papervizagent/blob/e088a8fff74cc363b6897c0843631fff76484908/utils/eval_toolkits.py#L139).

## Upstream bugs not copied

The original Retriever intends to fall back to no references, but Planner can
still reopen a missing ref.json. Invalid Critic JSON defaults to acceptance.
Visualizer hardcodes three critic entries while the UI permits five rounds.
The port records these failures/limits explicitly instead. It also does not
describe a final round-limit image as independently approved unless a Critic
actually examined that image.

## Evidence and limits

[UPSTREAM.json](UPSTREAM.json) records source and vendored-file hashes.
[Behavioral evaluation](evals/README.md) separates observed live runs from
unexecuted cases. Structural installation checks alone are not evidence of
multi-agent fidelity or scientific figure quality.

[Official Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
confirms that skill instructions can request native delegation and that agents
inherit the parent model/effort when not overridden. The plugin therefore
requires no custom-agent files, OAuth token handling, or model configuration.
