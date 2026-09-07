# Shared title/caption regression

The [original native run](../native-pipeline/README.md) exposed conflicting
instructions: the Planner and Stylist requested in-artwork titles/captions,
while the Visualizer prohibited the title and the Critic preserved it.

Two fresh isolated native role invocations received the updated shared adapter
and the original failing inputs. The [Stylist description](stylist-description.md)
now removes both overall title and caption from the artwork. The independent
[Critic](critic.json) actually inspected the old image, identified both defects,
and returned a complete description without their contradictory placement or
font instructions. Scientific connections and both meaningful legend entries
remain intact. The parent task checked both complete outputs.

[Run record](run.json), [Stylist provenance](stylist-report.md), and
[Critic provenance](critic-report.md) record the actual inputs and agent IDs.
Machine-specific paths in provenance reports were replaced with relative paths;
role output files were preserved unchanged.

This passes the targeted text regression. No image calls were made, so this test
does not establish that a subsequent render will obey the revised description.
