# Native full-mode execution evidence

This synthetic test used five fresh native role invocations: Planner, Stylist,
two Visualizers, and one Critic. Retrieval was explicitly disabled for this
bounded test. Each worker received only its assigned role prompt and inputs;
there was no inherited conversation history and no API-key setup.

Exactly two native image calls produced the [planner render](candidate-01/figure-planner.png)
and [styled render](candidate-01/figure-stylist.png). The Critic inspected the
actual styled image and requested a revision. The run stopped with
`budget_exhausted`, not acceptance; the complete revision was saved without a
third image call.

The [run record](run.json), [exact artifact hashes](artifact-manifest.json),
[validation](validation.json), and [detailed review](candidate-01/review.md)
retain real agent IDs, inputs, prompts, artifacts, and unresolved defects.
The parent task also inspected both saved images and confirmed the reported
scientific structure and title/caption/connector defects.

This run exposed conflicting title/caption instructions between roles. Its
original descriptions, image prompts, images, and critique are preserved
unchanged. The final v0.2 adapter shares one placement constraint across roles
and checks it before rendering; a separate text-only regression test exercises
that fix. These images predate the fix and are not evidence that it has been
rendered successfully.

Only public synthetic inputs and generated figures are included. Machine-specific
cache paths and tool output hints were removed from render metadata; run paths
were made relative. Published hashes below describe these sanitized records.
Upstream role guidance is copied unchanged with attribution.
