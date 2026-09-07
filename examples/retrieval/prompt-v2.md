Use case: precise-object-edit

Asset type: targeted revision of a scientific methodology figure

Input image: `figure-v1.png` — edit target

Primary request: Change only the rounded component card currently labeled "Generator". Change its label to exactly "Answer generator" and change its fill from pale blue to pale orange. Keep the component's size, position, rounded outline, arrows, and typography consistent with the original figure.

Text (verbatim): Replace "Generator" with "Answer generator". Preserve all other existing text exactly as shown.

Constraints / invariants: Do not alter any other scientific label, component, icon, arrow, arrow direction, group, boundary, color, or layout. Preserve the dashed "Inference time" boundary; Question; Frozen question encoder and its Frozen status; Query vector; Nearest-neighbor retriever; Read-only document index and its lock/Read-only state; exactly five visually distinct retrieved-passage cards and the "5 retrieved passages" label; the index-to-retriever connection; the lower Question-to-Answer-generator connection; the passage-to-Answer-generator connection; and the final "Answer with passage citations" output. Preserve inference-only scope. No training, updates, reranking, web search, verification, metrics, new modules, or extra passage cards.

Avoid: Changing any text other than the single requested replacement; changing scientific relationships; moving or redrawing connectors; altering frozen/read-only semantics; adding captions, titles, logos, watermarks, people, robots, or decorative content.
