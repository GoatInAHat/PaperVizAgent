# Faithfulness and explicit adaptations

Pinned official source: google-research/papervizagent
at e088a8fff74cc363b6897c0843631fff76484908. The original agents are separate
role-specific model calls orchestrated in one Python process. This port uses
fresh native Codex subagents and persisted artifact handoffs.

## Restored from v0.1.0

- Actual separate role contexts and independent per-round Critic input.
- Ranked real reference examples and multimodal Planner input.
- Original unabridged task-specific prompts and both complete style guides.
- Named pipeline modes, separate planner/stylist artifacts and both initial
  renders in full mode.
- Three critic rounds by default; strict structured results; complete
  description regeneration instead of bitmap edits inside that loop.
- Plot-specific planning, styling, rendering, and render-error critique.
- Recorded execution state, stage provenance, stop reasons, and resumable runs.

## Deliberate differences

- Models and inference transport: the runtime resolves each role/modality from
  explicit configuration first, then verified host-native tools, then an
  available Codex capability only for the missing modality. Configured provider
  calls are fresh per-role requests/threads; host-native calls are fresh
  subagent contexts. The original Python processor is not running. A host name
  alone does not establish text, vision, delegation, or image capability, and
  model sampling, exact pixel resolution, and benchmark parity cannot be
  promised.
- Configuration and settings: runtime configuration is loaded from the
  `PAPERVIZAGENT_CODEX_CONFIG` JSON/YAML path and environment, never from an
  authentication-token argument. The adapter passes complete upstream request
  data/settings to the resolved provider or native tool, then applies only
  explicit allowed overrides.
- Defaults: one full-pipeline candidate suits a conversational request. The
  original Streamlit demo defaults to ten planner+critic candidates, 21:9.
  Those are UI defaults, not universal algorithm settings. User overrides
  select the pipeline, candidates, size, and image budget without a config file.
- Reference delivery: the pinned author's public Space exposes the same pool
  schema as individual files. Fetch metadata/selected images at use instead of
  bundling or downloading the entire dataset ZIP. Missing/network-blocked
  retrieval is explicitly recorded as none. The complete candidate set is read
  in batches with retained ranked shortlists to fit native context limits; this
  differs from upstream's single huge retrieval prompt. Manual/random benchmark
  ablations remain outside this helper; supplied references are a separate mode.
- Caption scope: when a user omits a caption, infer and explicitly label a
  proposed caption. The original demo requires a supplied caption.
- Shared handoff constraints: make caption/title placement consistent across
  roles and reject contradictory descriptions before rendering. Original
  aesthetic-preservation instructions cannot retain an unwanted figure title.
- Semantic safeguards: preserve meaningful legends despite the original
  critic's blanket suggestion to remove them, and allow a documented rollback
  if final scientific content regresses.
- Outputs: keep the host's actual PNG or other format and source artifacts;
  do not force upstream's base64 JPEG conversion. Native editable SVG is an
  additional, explicitly requested renderer.
- Scope: no Streamlit UI, benchmark runner, baseline comparisons, or claims of
  the paper's scores. The qualitative Critic is not the separate
  ground-truth evaluation in upstream utils/eval_toolkits.py.

## Upstream defects intentionally not reproduced

- No-reference fallback must not reopen a missing ref.json in Planner.
- Invalid Critic JSON must fail the review, not become "No changes needed."
- A user-requested round limit above three must not be silently ignored by a
  hardcoded three-entry render loop.
- A final round-limit render is not independently approved unless another
  Critic actually examined it.

These adaptations are reported rather than hidden behind a claim that this is
the unmodified official implementation. See the root FIDELITY.md for source
evidence and the evaluation record for what has actually run.
