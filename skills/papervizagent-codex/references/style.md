# Style without changing the science

Adapted from Google Research PaperVizAgent's stylist and diagram style guide.
Copyright 2026 Google LLC. Modifications copyright 2026 PaperVizAgent-codex
contributors. Apache-2.0; see NOTICE and UPSTREAM.json.

Preserve content, connections, state, and scope. Refine the planned description
instead of replanning the method. Preserve a user's chosen style and effective
existing aesthetics; do not enforce a conference's supposed house style.

When no style is specified:

- Use a white or very light background, generous spacing, and clear reading order.
- Group related stages with subtle fills or boundaries; use color consistently
  for one meaning, reinforced by labels, shape, or line style.
- Use a small, legible palette. Suitable defaults include dark slate text
  (`#243247`), pale blue (`#E6F3FF`), pale mint (`#E0F2F1`), and a restrained warm
  accent (`#C75B12`). Check contrast at the intended display size.
- Use consistent sans-serif component labels and clearly rendered mathematical
  notation. Prioritize small-size readability over decorative detail.
- Keep connector endpoints unambiguous. Route crossings around labels, and use
  distinct line styles only when their semantics are defined.
- Preserve necessary legends. A legend is useful when color, symbols, or line
  styles encode information that cannot be understood from nearby labels.
- Keep icons sparse and semantically grounded. A lock or snowflake means frozen
  only if the source or legend establishes that meaning. Avoid decorative robots,
  flames, or 3D objects unless they help the requested illustration.
- Keep figure captions external by default. Do not add journal logos, venue
  branding, citation badges, or claims of publication approval.

For user-supplied sketches, preserve the intended relationships while improving
alignment, spacing, labels, and visual hierarchy. If aesthetic cleanup would
change a scientific connection, resolve the content first.
