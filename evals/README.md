# Behavioral evaluation

[cases.json](cases.json) contains realistic requests and observable acceptance
criteria. Package validation alone does not establish figure quality.

Run each case in a fresh Codex task with the installed plugin, using the case's
request and the provided source file. The revision case continues the raster
case. Save evaluation output outside the source tree unless you deliberately
choose a reviewed example for publication.

Record:

- Codex model and available native image capability, as actually observed.
- Tools used, number of image calls, and whether any key or provider setup was
  requested.
- Real artifact paths, the specification, exact prompts, and visual review.
- Pass/fail/partial against each criterion, with observed defects.

For the unavailable-tool case, run in a context where the tool is absent or
explicitly impose that condition. This checks graceful behavior; it does not
test the image backend. For plots, compare the source values and rendered marks.
For SVG, inspect the XML and actual rendering, not only the file extension.

Live image tests consume the signed-in user's included Codex usage. They are
kept separate from credential-free CI and are not run automatically on every
pull request. The maximum one-call smoke budget is part of the request.

## Recorded smoke run — 2026-09-07

A fresh delegated Codex agent (GPT-5.6 Terra, medium reasoning) read the candidate
skill and the synthetic method. It used the host's built-in image-generation
tool once, then continued with one built-in edit call. No API key, provider
configuration, or additional model process was used. The backend image-model
identifier was not independently exposed by the observed tool result.

| Case | Observed result | Evidence |
|---|---|---|
| Method to raster | Pass: required labels, eight connections, frozen/read-only states, five passages, actual saved PNG and visual inspection | [v1](../examples/retrieval/figure-v1.png), [spec](../examples/retrieval/figure-spec.md), [prompt](../examples/retrieval/prompt-v1.md) |
| Targeted revision | Pass for requested label/color and scientific invariants; minor unrequested card-geometry/outline drift | [v2](../examples/retrieval/figure-v2.png), [prompt](../examples/retrieval/prompt-v2.md), [review](../examples/retrieval/review.md) |
| Unavailable tool | Not run in this smoke evaluation | Case retained for follow-up |
| Editable diagram | Not run in this smoke evaluation | Case retained for follow-up |
| Data-grounded plot | Not run in this smoke evaluation | Case retained for follow-up |

Both PNGs are 1774 × 887. A parent agent also inspected both actual outputs.
The visible duplicate Frozen annotation and ellipsis query-vector glyph are
minor presentation limitations. These two cases demonstrate the workflow; they
are not a benchmark or a guarantee for arbitrary papers.

## v0.2 native-agent verification — 2026-09-07

The original v0.1 run above remains historical evidence for native image
generation and user editing only. It did not test independent role contexts.

The revised tests use actual native Codex subagents with no inherited
conversation history and the pinned original role prompts. No model API client
or OAuth credential reader is used. Exact observed artifacts and stop states
are recorded below; these are workflow checks, not benchmark scores.

- Reference helper: nine standard-library tests cover full-content pool scope,
  ranked selected-image materialization, cache integrity, invalid IDs, bounded
  download, path containment, and offline failure. A live pool download retained
  all first-200 diagram records; one selected image was downloaded, verified as
  a real 1887 × 833 JPEG, and visually inspected. Both metadata files also match
  the official dataset ZIP byte-for-byte, including record ordering. This tests
  the data path; it does not benchmark native ranking across all 200 examples.
- Vendored source: all 16 role prompts match the original Python constants;
  both complete style guides match their upstream files byte-for-byte. Two
  automated distribution checks cover recorded hashes and local links.
- Independent Critic → Visualizer: a fresh Critic detected a five-versus-three
  passage error from the actual image, returned a complete revised description,
  and a separate fresh Visualizer rendered from that text without an image-edit
  target. Exactly one image call corrected the visible count and printed label.
  The result remains partial against the complete visual specification: an
  inference-time label is missing and one connector is routed differently.
  [Source, outputs, prompts and execution record](../examples/critic-correction/README.md).
- Full pipeline with retrieval explicitly disabled: five fresh role invocations
  produced separate Planner/Stylist descriptions, two actual initial renders,
  and an independent visual Critic result. The exact two-image budget stopped
  further rendering with `budget_exhausted`, preserving the requested revision.
  The source science was preserved, but title/caption placement and one connector
  remained defective. This run exposed a cross-role instruction conflict and
  is recorded as partial, not accepted.
  [Complete native execution evidence](../examples/native-pipeline/README.md).

- Shared title/caption constraint: fresh Stylist and Critic workers received the
  original failing artifacts and the updated adapter. Both removed contradictory
  title/caption rendering, placement, and font instructions while retaining the
  science. Critic inspected the actual old image. This passes the text regression;
  no subsequent image was generated.
  [Role outputs and provenance](../examples/title-handoff/README.md).

The unavailable-delegation, malformed-Critic/missing-image, explicit SVG and
Matplotlib plot cases remain specified but have not been executed as live
agent evaluations in this release. Native ranking quality, multiple candidates,
and the full three-regeneration default also need broader evaluation.
