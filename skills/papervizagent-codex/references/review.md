# Visual critique and targeted revision

Adapted from Google Research PaperVizAgent's diagram/plot critic and evaluation
dimensions. Copyright 2026 Google LLC. Modifications copyright 2026
PaperVizAgent-codex contributors. Apache-2.0; see NOTICE and UPSTREAM.json.

Inspect the rendered image, not just the prompt. Compare it to the original
source, figure intent, and invariant list. Report concrete observations.

| Dimension | Check |
|---|---|
| Faithfulness | Required elements are present; no invented components or claims; arrow direction and endpoints match the adjacency list; group/state semantics are correct; values and notation match the source. |
| Conciseness | No duplicated modules, repeated explanations, unnecessary decorations, or content outside the caption's scope. Preserve necessary legends. |
| Readability | Every label is legible at intended use size; spelling is correct; arrows do not cross text; math is readable; small details and panel ordering remain distinguishable. |
| Aesthetics | Consistent typography, alignment, spacing, palette, border weights, and visual hierarchy appropriate to the user's style. |

Prioritize scientific defects over cosmetic preferences. State uncertainty if
small text, unsupported context, or insufficient source evidence prevents a check.
Don't assert scientific correctness simply because the image looks plausible.

For a correction, name the defect and location, the exact desired change, and
the elements that must remain fixed. Correct from the previous best image when
possible. Use a fresh complete prompt only if the composition itself is defective.

After each correction, recheck all scientific invariants, not only the requested
edit. Previous successful edits can disappear. Keep the best candidate and explain
why it was selected. If the allowed correction budget ends, return the best
candidate with remaining issues plainly stated.

Suggested review record:

```text
Candidate: figure-v1.png
Inspected: actual image at full view and label scale
Faithfulness: observed matches and defects
Conciseness: observed matches and defects
Readability: observed matches and defects
Aesthetics: observed matches and defects
Next action: accept, targeted edit, or blocked; with reason
Selected final: candidate path and reason
Unresolved issues: specific items, or none observed in these checks
```

This is a qualitative review. Do not invent numerical scores, human preferences,
comparisons with the upstream benchmark, or guarantees of publication acceptance.
