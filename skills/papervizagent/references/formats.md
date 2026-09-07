# Plot and editable renderers

Both formats retain the same separate Retriever, Planner, optional Stylist,
Visualizer, and Critic contexts as the main pipeline. Select the plot-specific
original role prompts for statistical plots; editable conceptual diagrams use
the diagram prompts with the explicit SVG renderer adapter.

## Statistical plots

The original renderer asks a model for Python Matplotlib code, executes it, and
preserves the source. Resolve its text/code modality from explicit configuration,
then an actually available host runtime, then Codex only if that modality is
missing and available there. Do not assume a system Python has Matplotlib or
install a model SDK.

Planner receives raw data plus visual intent and actual selected reference
plots; its description must enumerate every value and visual mapping. Stylist
reads the complete original plot guide and preserves all values. Visualizer sends
complete upstream visualizer data/settings and permitted overrides to the
resolved role, writes runnable Matplotlib source from the complete description,
executes it, and retains the raw input, source, output, and any error. Save requested SVG/PDF
in addition to a raster preview when the installed renderer supports them.

Check values, categories, scales, units, aggregation, and supplied uncertainty.
Do not infer hidden measurements, confidence intervals, significance, or sample
sizes. Missing raw data prevents a quantitative plot; distinguish a conceptual
sketch rather than fabricating results.

Feed actual plot/code failures into a fresh Critic as explicitly missing-render
input. Critic can repair the description, then Visualizer writes/executes new
source; text-only failure review must not be called visual inspection.
Successful execution alone does not validate quantitative accuracy.

If Matplotlib is unavailable, report that renderer limitation. An explicitly
requested simple editable SVG may use native SVG code from the same data, with
the substitution recorded; do not silently claim the original renderer ran.

## Native editable SVG diagrams — additional renderer

For an explicit vector request, Visualizer uses the same modality-resolution
order to author text/path/shape elements from the current complete description.
Parse the XML and inspect an actual rendering with available host tools. Critic
receives that rendering and the same source/description contract. A subsequent
regeneration produces new SVG source, preserving the previous version.

Do not wrap a raster in SVG and call it editable. Disclose any embedded raster
illustrations. This renderer is an added Codex capability, not an implementation
of SAM, AutoFigure-Edit, CraftEditor, or lossless bitmap vectorization.
