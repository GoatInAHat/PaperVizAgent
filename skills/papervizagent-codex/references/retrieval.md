# Native reference retrieval

The Retriever uses the active Codex model to select relevant examples. The
Python standard-library helper only fetches public reference files; it has no
model client, credentials, packages to install, or provider configuration.

Run the helper with Python 3.9 or newer. Choose a reference directory inside the
figure's run directory and use its absolute path in place of `RUN_REFERENCES`:

```sh
python3 scripts/fetch_references.py pool --task diagram --output-dir RUN_REFERENCES
```

Resolve `scripts/fetch_references.py` relative to this skill's directory. Use
`--task plot` for data plots. The helper downloads and verifies the metadata,
then writes a pool manifest and full-content batches of ten examples. It uses
the first 200 diagram records, or all 240 plot records, matching upstream auto
retrieval. Read every listed batch; never silently replace complete methods or
data with title-only matching. Batches let the native Retriever process a pool
that may exceed one context window. Preserve ranked shortlists and reasons
between batches, then compare finalists to select ten exact IDs (or all eligible
examples if fewer than ten exist). Smaller batches are available through
`--batch-size`; this changes context packaging, not the candidate set.

For diagrams, rank same topic **and** visual intent highest; then prioritize
matching visual structure over topic alone. A framework, pipeline, or detailed
module needs a structurally appropriate example. For plots, match data
characteristics and plot type first, then compatible data with the same plot
type. Avoid mismatched diagram/plot types. Preserve the ranking and reasons in
the run's retrieval record.

Materialize the selected examples, using the actual ranked IDs:

```sh
python3 scripts/fetch_references.py select --task diagram --output-dir RUN_REFERENCES --ids ref_1 ref_25
```

The command above illustrates two IDs; the normal Retriever selects ten.
The selected-reference manifest contains each complete source method or raw
dataset, caption/intent, original metadata, and a saved image's path, source URL,
dimensions, byte count, and SHA-256. **The Planner must open each selected image**
and learn from the paired source + caption + actual image. Merely listing
reference IDs or inspecting the metadata does not complete reference retrieval.
Never import a reference paper's scientific content into the target method.

Downloads cache under `RUN_REFERENCES/.reference-cache`; `--cache-dir` optionally
reuses an explicit cache directory. Pinned metadata hashes and image checksums
are validated before cache reuse. Only selected images download (at most ten,
20 MB each); the entire archive and test split are not downloaded. Offline or
invalid-data failures are explicit. Record a degraded no-reference run if public
files are unavailable, or use supplied references with their provenance; do not
report successful benchmark retrieval. If Python is unavailable, host-native
fetch tools may retrieve the same pinned metadata and selected images while
preserving the full candidate scope, input pairs, and provenance.

## Source and rights

The authoritative code is [Google Research PaperVizAgent at the pinned revision](https://github.com/google-research/papervizagent/tree/e088a8fff74cc363b6897c0843631fff76484908),
formerly PaperBanana. The public data source is the original author's
[PaperBanana Space](https://huggingface.co/spaces/dwzhu/PaperBanana), pinned at
`587f33ecd98649a4588ff22c1bc3a865f6d8e3b4`. Its README declares Apache-2.0
and it contains the same Apache license as the code repository. This declaration
does not establish separate licenses for every underlying third-party paper
figure. Downloaded references retain their original provenance; this plugin
does not bundle the corpus or relicense those figures.

Pinned metadata:

- [Diagram references](https://huggingface.co/spaces/dwzhu/PaperBanana/resolve/587f33ecd98649a4588ff22c1bc3a865f6d8e3b4/data/PaperBananaBench/diagram/ref.json):
  298 records, 4,496,771 bytes; SHA-256
  `d978569bbd46c1d312cde669475b87ace868d80bfb7ffb0484464dbc6b8f5d6a`.
- [Plot references](https://huggingface.co/spaces/dwzhu/PaperBanana/resolve/587f33ecd98649a4588ff22c1bc3a865f6d8e3b4/data/PaperBananaBench/plot/ref.json):
  240 records, 900,781 bytes; SHA-256
  `f2f169f49ed84fc1b65cb5c5d48163d29b87e67a736721e6bf04dd4c5954da28`.

Images resolve beneath the same task directory using the URL-encoded
`path_to_gt_image` from the pinned metadata. The separate
[PaperBananaBench dataset](https://huggingface.co/datasets/dwzhu/PaperBananaBench)
currently provides a 265,846,711-byte ZIP without a dataset card or a separate
license file in the archive; the extracted author Space avoids that full download.
