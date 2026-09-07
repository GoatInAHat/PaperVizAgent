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
