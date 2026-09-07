# Editable diagrams and quantitative plots

Use this reference only for a requested editable format or a quantitative plot.

## Editable SVG diagrams

For an explicit SVG/vector request, use the active Codex model to author actual
SVG elements for labels, shapes, and connectors, then render and inspect them
with the host's available browser or image tools. Preserve source evidence,
invariants, and review history as in the main workflow. Parse the SVG as XML and
inspect the rendered output; valid XML alone doesn't establish visual quality.

Represent editable components with native text/path/shape elements. Do not embed
a full raster figure in an SVG and describe it as editable. Disclose any embedded
raster illustrations and their limits. If faithful vector reconstruction of an
existing bitmap isn't feasible with the available tools, explain what can and
cannot be made editable rather than promising lossless conversion.

This direct SVG path is an added Codex capability. It is not PaperVizAgent's
original raster pipeline, AutoFigure-Edit, or CraftEditor, and it uses no SAM
server or raster-to-vector model.

## Statistical plots

Use executable plotting code with the user's actual data, following
PaperVizAgent's code-rendered plot approach. Do not ask an image model to invent
or redraw quantitative marks. Use an installed plotting library when available;
for a simple chart, native SVG from the data is also suitable. Do not install a
model SDK or request inference credentials.

Preserve the data and runnable plotting source alongside the output. Explicitly
map columns/variables to axes, units, groupings, and aggregation. Derive values
from supplied data; do not infer hidden samples, uncertainty intervals, statistical
significance, or missing measurements. If raw values are unavailable, ask for
them or clearly distinguish a conceptual schematic from a quantitative result.

Check the plotted values, category order, axis domains and scales, units,
uncertainty intervals where supplied, labels, and legends against the input.
Inspect the resulting graphic at its intended display size. Keep SVG/PDF exports
when supported and requested. Report the renderer and any unavailable dependency
instead of claiming an export succeeded.
