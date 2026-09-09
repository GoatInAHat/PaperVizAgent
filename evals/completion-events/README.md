# Completion-event verification

Live smoke run on September 9, 2026 with official Codex SDK managed sign-in.
The account catalog verified `gpt-5.6-luna` with low effort; this override was
confined to the smoke configuration and did not change product defaults.

The real upstream VanillaAgent generated an `Input → Transform → Output`
diagram through `generate_events`. The consumer received exactly six pushed
events: run started, candidate started, role started, role completed, candidate
completed, run completed. Sequences were contiguous and run/candidate/call IDs
matched. Candidate files existed before candidate completion, and the trace
existed before run completion. The final result retained `candidates` and `trace`.
No timer, status query, scheduled follow-up or generation retry was used.

Exactly one image call, one small text call and one image-input vision call ran
in three distinct ephemeral Codex threads:

| Role/modality | Thread ID |
|---|---|
| Planner / text | `01a08826-321b-7803-9584-8694a254ce25` |
| Vanilla / image | `01a08826-4275-7e92-9479-73559e582fd4` |
| Critic / vision | `01a08827-07ec-7220-bc23-7a56d1f676ea` |

The text check returned `EVENT_OK`; the vision check correctly read the three
labels and two rightward arrows. The actual artifact was also visually inspected.
Vanilla mode has no critic loop: its stop reason was null, not critic approval.
The vision call was a label-reading smoke test, not a full Critic acceptance.

The final change also passes 44 tests and 52 parameterized subtests. They cover
concurrent correlation, queued-candidate timing, partial results, failure
notifications, cancellation and iterator cleanup. The queued-candidate event was
moved inside the semaphore after the live smoke; that concurrency correction
was verified with a gated regression test, without another paid image run.
An independent skill forward-test confirmed one background coordinator, return
of main-session control, and delivery through the native completion channel.

Build/check, skill validation and package generation passed. The wheel was
inspected for the exact updated runtime files. This smoke does not establish
new transport-level progress support, API-provider coverage or benchmark scores.
