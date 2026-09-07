# Pipeline, state, and refinement

Default mode is `full`, chosen to expose all five original roles. Accept
`planner_critic`, `planner_stylist`, `planner`, `vanilla`, `retriever`, and
`polish` when requested. Upstream dev_/demo_ aliases select the corresponding
role graph here, but do not implicitly claim benchmark evaluation.

| Mode | Role graph | Initial description renders |
|---|---|---|
| full | Retriever → Planner → Stylist → Visualizer → Critic/Visualizer loop | Planner **and** Stylist |
| planner_critic | Retriever → Planner → Visualizer → Critic/Visualizer loop | Planner |
| planner_stylist | Retriever → Planner → Stylist → Visualizer | Planner and Stylist |
| planner | Retriever → Planner → Visualizer | Planner |
| vanilla | Separate native direct-generation worker using upstream/<task>-vanilla.md | Direct request |
| retriever | Retriever only | None |
| polish | Separate suggestion worker, then native image-edit worker | Edited original |

A requested candidate count creates independent candidate directories and role
contexts. Reuse the downloaded reference pool, but preserve each candidate's
retrieval decisions and descriptions. Run independent candidates in parallel
only within the host's available agent/image capacity; otherwise run sequentially.
One candidate is the conversational default; the original demo defaults to ten.

## Run directory and state

Save raw source/data and caption once, then for each candidate retain:

```text
run.json
source.md or data.json
caption.txt
candidate-01/
  retrieval.json
  planner-description.md
  stylist-description.md                 # only when selected
  prompt-planner.md, figure-planner.png
  prompt-stylist.md, figure-stylist.png    # only when selected
  critic-0.json, critic-description-0.md
  prompt-critic-0.md, figure-critic-0.png
  ...                                    # actual rounds only
  review.md
```

Use actual file extensions. Plot files additionally include runnable source and
the raw data mapping; render failures are stored as error text. Save selected
reference content/images under the run or an existing host cache, with source
URLs, IDs, and hashes. Do not write user runs into the installed plugin.

The coordinator owns `run.json`; workers own only assigned output files. Record:

- schema_version: 1; upstream_revision; mode; task; requested retrieval mode;
  candidate count; max_critic_rounds (default 3); image budget if requested.
- Per role invocation: role, stage/round, real agent ID, context isolation used,
  input paths, output paths, status, and any tool bridge.
- Per candidate: retrieval status and selected IDs; every render's description,
  exact prompt, real output or failure; every critic result and its input image;
  current_critic_round; selected_image; stop_reason; unresolved limitations.
- Actual image call count, including unsuccessful calls; skipped stages and
  their reason. Never fill in fabricated agent IDs or expected file paths as
  completed outputs.

Paths in public/shared records should be relative to the run, with original
external URLs retained where relevant. Local working paths may be absolute.

## Description handoff check

Before rendering a planner, styled, or critic description, check that its title/
caption instructions agree with the shared adapter and user constraints. If
not, record `description_conflict` and return the artifact to a fresh invocation
of its authoring role with the original inputs plus the specific failed
constraint. Preserve both versions. This is a recorded text repair, not another
image call or an independent image-critique round. Allow one repair for that
handoff; if the conflict persists, stop with that failure and keep artifacts.
Do not silently rewrite the role output in the coordinator or send contradictory
render instructions.

## Critic loop

Start with the styled image/description in full mode, the planner pair in
planner_critic. If the required initial diagram render is missing, stop with
`render_failed`; retain any valid earlier planner render as an explicitly
incomplete fallback. Do not start a visual critique on a nonexistent diagram. The planner render is an evolution artifact in full mode, not
an automatic competitor to the styled output.

For round indices 0 through max_critic_rounds-1:

1. Dispatch a fresh Critic with the exact current description and actual image,
   plus the raw target source and caption. If plot rendering failed, pass its
   error and explicitly request the original text-only failure-repair behavior.
2. Parse the returned JSON and require two nonempty strings. Missing/invalid
   output sets `critic_failed` and preserves the last valid image; it cannot
   stop with acceptance. A retry must be recorded, not disguised as an ordinary
   completed round.
3. Stop with `accepted` only when trimmed `critic_suggestions` equals
   `No changes needed.` **and a real current render was successfully inspected**.
   Without that render, acceptance is invalid: record `critic_failed` and the
   missing-image limitation. Otherwise keep the current description/image.
4. Otherwise `revised_description` must be a complete usable description, not
   merely edit instructions or the no-change sentinel. Save it separately.
5. If the user's image-call budget is exhausted, stop with `budget_exhausted`,
   preserve the critique and revised description for resumption, and report
   unresolved defects.
6. Dispatch Visualizer for fresh generation from the revised text. Do **not**
   submit the previous image as an edit target. On rendering failure preserve
   the previous valid result and stop with `render_failed`.
7. Set current image/description to the successful new pair. At the round limit
   stop with `round_limit`, not `accepted`; the last regeneration has not been
   reviewed by another independent Critic unless a further round actually ran.

Upstream chooses the latest successfully rendered candidate and rolls back on
render failure. This port adds a final coordinator semantic check: inspect the
real final artifact, and revert to a prior valid pair if a scientific regression
is observed. Record `regression_rollback`, the evidence, and remaining defects.
This safeguard is distinct from a fabricated additional independent critique.

The default three rounds allow at most three critic-driven regenerations. Full
mode also retains two initial renders (up to five image calls per candidate).
Count attempted calls against an explicit user budget and the announced maximum.
There are no automatic retries of failed visible image-tool calls; a requested
retry needs remaining budget and its own recorded attempt. If a smaller budget
cannot cover both initial renders, prioritize the styled result, mark the
planner render `skipped_budget`, and describe the run as budget-limited.
Do not silently increase rounds, candidates, or calls.

## Explicit editing and polish

A user-requested change to an existing bitmap is a different path from the
generation critic loop. Inspect it, read any prior run/specification, and save
the user's exact change and invariants. A separate native edit worker invokes
image editing with that bitmap as target, saves a new version, and inspects it.
A separate Critic can check the resulting scientific content when source exists.
Do not promise unchanged pixels outside the requested region.

For requested automatic aesthetic polish (`polish`), first dispatch a separate
worker with `upstream/<task>-suggestion.md`, the image, and the complete
`upstream/neurips2025_<task>_style_guide.md`; then an edit worker
with those suggestions and `upstream/<task>-polish.md`. This mirrors the
upstream suggestion-plus-edit path. User-specified exact edits need not add an
unrequested aesthetic redesign. Upscale/size only when the native tool supports
it, and report actual dimensions.

## Failure and resumption

Keep stage status separate from artifact existence. Unavailable native agents,
images, network, or plot libraries are explicit limitations. Retrieval may
degrade to none as upstream intends; do not pretend retrieval ran successfully.
An unavailable image backend preserves completed descriptions and prompt.

On resume, use saved source/description and the next required stage. Preserve
prior role results; create new files and fresh role contexts for repeated stages.
Never start an alternate model provider or infer nonexistent measurements.
