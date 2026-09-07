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
- `P1` — a grouped stack labeled exactly **3 retrieved passages** with exactly three clearly distinct pale-mint passage cards. Correct the current rendered five-card stack by removing two cards and replacing the incorrect **5 retrieved passages** label with **3 retrieved passages**. Arrange the three remaining cards in one evenly spaced vertical column, centered on the main pipeline axis. Each card has a small outline document icon and two short, nonverbal horizontal text strokes. Fit a single grouping brace to exactly these three cards; the brace must not enclose empty slots or suggest hidden additional cards.
- `G1` — a component labeled exactly **Generator**.
- `A1` — output card labeled exactly **Answer with passage citations**.

Connections:

- `Q1 -> E1`: question data, left to right.
- `E1 -> V1`: query vector, left to right.
- `V1 -> R1`: query, left to right.
- `I1 -> R1`: access to the read-only document index; line points from index toward retriever.
- `R1 -> P1`: three retrieved passages, left to right. Align the incoming arrow with the vertical center of the corrected three-card group; the arrow stops before the cards.
- `Q1 -> G1`: original question is also consumed by the generator; use a clearly routed lower arrow.
- `P1 -> G1`: three retrieved passages, left to right. Draw one arrow from the midpoint of the brace enclosing exactly the three cards into the generator. Keep this passage-input arrow visually separate from the original-question arrow entering the generator from below.
- `G1 -> A1`: answer with citations, left to right.

Groups and state:

- One subtle dashed or rounded enclosure labeled **Inference time** around the entire workflow.
- `E1` is frozen at inference. `I1` is read-only at inference.
- `G1` consumes both the original question and the retrieved passages.

Layout and style:

- Pipeline layout, left to right: `Q1`, `E1`, `V1`, `R1`, `P1`, `G1`, `A1`.
- Place `I1` above or below `R1`, attached by a short unambiguous arrow into `R1`.
- Route the `Q1 -> G1` arrow along the bottom, avoiding text and other arrows.
- White background; dark slate text; pale blue for encoder/retriever and generator; pale mint for index/passages; restrained warm orange accent for the answer/citations. Use clean scientific-vector infographic styling, flat two-dimensional shapes, consistent sans-serif typography, tidy alignment, and no in-image title or caption. Preserve the current readable scale, rounded rectangles, thin dark outlines, uniform arrow strokes and filled triangular arrowheads. Match all three passage cards in width, height, corner radius, outline thickness and internal icon style.
- Preserve the nearby **Read-only** lock and **Frozen** snowflake annotations: they encode scientifically meaningful inference-state constraints. Include a tiny key only if these meanings cannot be made clear by the nearby labels; retain any scientifically meaningful legend needed to interpret states or encodings.

Invariants:

- Exactly three retrieved passages are depicted and described.
- The question encoder is frozen, and the document index is read-only.
- The generator receives both the original question and three retrieved passages.
- The index supplies retrieval access; it does not receive writes or updates.
- No training loop, reranker, web search, verification stage, metrics, unsupported algorithms, invented numerical values, or decorative robots appear.
- Keep the caption outside the image.

Uncertainties: The source does not state the retriever's internal algorithm beyond nearest-neighbor retrieval; therefore no algorithmic label such as BM25 or vector search is permitted. The source does not specify a generator architecture.

References: No visual reference image supplied. Layout follows the supplied authored pipeline-planning heuristic and style guide.

