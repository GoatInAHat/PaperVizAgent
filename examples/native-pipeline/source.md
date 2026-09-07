# Evidence-grounded answer generation

At inference time, a user submits a question. A frozen question encoder maps the
question to a query vector. A nearest-neighbor retriever uses that vector to
select five passages from a document index. A generator consumes both the
original question and those five passages, then produces an answer with passage
citations. The document index is read-only during inference. This figure does not
describe training, reranking, web search, or a verification stage.

Desired caption: Inference workflow for answering a question with citations to
five passages retrieved from a read-only document index.
