# Figure specification

Source: source.md

Intent and caption: **Inference workflow for answering a question with citations to three passages retrieved from a read-only document index.** The figure depicts only inference; it excludes training, reranking, web search, and verification.

Output format and intended display size: A polished landscape raster methodology diagram for a paper column or slide. Use generous spacing and labels readable at ordinary on-screen viewing size.

Required elements:

- `Q1` — input card labeled exactly **Question**.
- `E1` — a component labeled exactly **Frozen question encoder**. It maps the question to a query vector; a small snowflake plus the word **Frozen** may convey frozen status.
- `V1` — a compact data token labeled exactly **Query vector**.
- `R1` — a component labeled exactly **Nearest-neighbor retriever**.
- `I1` — a database/index store labeled exactly **Read-only document index**, visually marked **Read-only** with a small lock. It is available during inference but must not be shown as updated or trained.
- `P1` — a grouped stack labeled exactly **3 retrieved passages** with three clearly distinct passage cards (not an arbitrary number).
- `G1` — a component labeled exactly **Generator**.
- `A1` — output card labeled exactly **Answer with passage citations**.

Connections:

- `Q1 -> E1`: question data, left to right.
- `E1 -> V1`: query vector, left to right.
- `V1 -> R1`: query, left to right.
- `I1 -> R1`: access to the read-only document index; line points from index toward retriever.
- `R1 -> P1`: three retrieved passages, left to right.
- `Q1 -> G1`: original question is also consumed by the generator; use a clearly routed lower arrow.
- `P1 -> G1`: three retrieved passages, left to right.
- `G1 -> A1`: answer with citations, left to right.

Groups and state:

- One subtle dashed or rounded enclosure labeled **Inference time** around the entire workflow.
- `E1` is frozen at inference. `I1` is read-only at inference.
- `G1` consumes both the original question and the retrieved passages.

Layout and style:

- Pipeline layout, left to right: `Q1`, `E1`, `V1`, `R1`, `P1`, `G1`, `A1`.
- Place `I1` above or below `R1`, attached by a short unambiguous arrow into `R1`.
- Route the `Q1 -> G1` arrow along the bottom, avoiding text and other arrows.
- White background; dark slate text; pale blue for encoder/retriever; pale mint for index/passages; restrained warm orange accent for the answer/citations. Use clean scientific-vector infographic styling, flat two-dimensional shapes, consistent sans-serif typography, tidy alignment, and no in-image title or caption.
- Include a tiny key only if the lock/snowflake meanings cannot be made clear by nearby **Read-only** and **Frozen** labels.

Invariants:

- Exactly three retrieved passages are depicted and described.
- The question encoder is frozen, and the document index is read-only.
- The generator receives both the original question and three retrieved passages.
- The index supplies retrieval access; it does not receive writes or updates.
- No training loop, reranker, web search, verification stage, metrics, unsupported algorithms, invented numerical values, or decorative robots appear.
- Keep the caption outside the image.

Uncertainties: The source does not state the retriever's internal algorithm beyond nearest-neighbor retrieval; therefore no algorithmic label such as BM25 or vector search is permitted. The source does not specify a generator architecture.

References: No visual reference image supplied. Layout follows the supplied authored pipeline-planning heuristic and style guide.
