Use case: scientific-educational

Asset type: polished scientific methodology figure for a research paper

Primary request: Create one clean, landscape, left-to-right scientific workflow diagram on a white background. Do not place a title or caption inside the image. Enclose the full workflow in a subtle rounded, dashed boundary labeled exactly "Inference time". Use flat 2D vector-infographic styling, generous white space, crisp thin dark-slate arrows, balanced alignment, and consistent dark-slate sans-serif text. Palette: pale blue for model/retrieval components, pale mint for document data, restrained warm orange for the final answer; no gradients, no 3D, no logos, no watermark.

Text (verbatim):
- "Inference time"
- "Question"
- "Frozen question encoder"
- "Frozen"
- "Query vector"
- "Nearest-neighbor retriever"
- "Read-only document index"
- "Read-only"
- "5 retrieved passages"
- "Generator"
- "Answer with passage citations"

Composition/framing: Main pipeline from left to right in this exact order: a question input card; a rounded pale-blue box for Frozen question encoder with a small snowflake and nearby word Frozen; a small token for Query vector; a rounded pale-blue box for Nearest-neighbor retriever; a visually grouped stack of exactly five pale-mint passage cards labeled 5 retrieved passages; a rounded blue Generator box; then a warm-orange output card Answer with passage citations. Place the pale-mint Read-only document index as a small database-cylinder above the retriever, with a tiny lock and nearby word Read-only. Draw the index-to-retriever arrow pointing into the retriever. Draw pipeline arrows question -> encoder -> query vector -> retriever -> 5 retrieved passages -> generator -> answer. Also draw a distinct, neatly routed lower arrow from Question into Generator so it is unmistakable that the generator consumes the original question as well as the passages. Arrowheads must be clear and arrows must never cross labels.

Constraints: Exactly five distinct passage cards must be visible in the retrieved-passages group. The frozen status applies only to the question encoder. The index is read-only and must have no write/update/training arrows. Show inference only. Preserve these semantics: question maps through a frozen encoder to a query vector; a nearest-neighbor retriever accesses the read-only document index and returns five passages; the generator consumes the original question plus the five passages and outputs an answer with passage citations.

Avoid: training loops, parameter updates, gradients, reranking, web search, a verification stage, metrics, equations, performance charts, unsupported retrieval algorithms such as BM25 or vector search, arbitrary numerical values, duplicated modules, decorative robots, people, logos, and captions inside the figure.
