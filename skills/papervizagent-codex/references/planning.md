# Planning scientific figures

Adapted from Google Research PaperVizAgent's diagram planner and retriever.
Copyright 2026 Google LLC. Modifications copyright 2026 PaperVizAgent-codex
contributors. Apache-2.0; see the repository's NOTICE and UPSTREAM.json.

The input is source methods plus a desired figure scope. Produce an explicit
description of the elements and their relationships before visual styling.

1. Map each required component to source evidence. Distinguish observed results,
   proposed methods, example inputs, and hypotheses.
2. Make an adjacency list of connections. Label what crosses each arrow: data,
   control, an objective, a gradient, a query, or a retrieved result. Preserve
   branches, loops, shared weights, and optional paths.
3. Choose the smallest layout that explains the intended claim:
   - **Pipeline:** ordered transformations, usually left to right.
   - **Parallel branches:** independent encoders or comparisons that later merge.
   - **Overview with detail:** a system panel plus a clearly linked module inset.
   - **Feedback loop:** execution path plus a distinct correction/update path.
   - **Before/after:** two aligned panels with the changed element emphasized.
4. Make literal label text explicit. Use shorter labels only if meaning survives.
   Keep the full expansion in the caption or specification if appropriate.
5. Specify meaningful state, grouping, and shape semantics. A frozen encoder is
   not an optional encoder; a dashed boundary is not a gradient path.

These layout choices are original heuristics for this adaptation. They are not
examples from the upstream benchmark. When the user supplies a reference image,
learn its spatial organization and style without importing its scientific content.

Do not use illustrative numbers, molecules, equations, attention maps, tensor
shapes, or performance bars unless supported by the source. If a source says
"retrieve relevant documents" but does not name an algorithm, don't label it
"BM25" or "vector search."

For an existing figure, keep stable element IDs and a short revision record.
Update the specification deliberately; don't append contradictory instructions
to an ever-growing prompt.
