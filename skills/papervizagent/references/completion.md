# Completion events

The host owns the background task and its lifetime. In an agent host with native
background completion, one coordinator runs the workflow outside the main
conversation and sends its final reviewed result through that host's completion
channel. Dependent roles start only after their inputs have actually completed.
Preserve the worker ID so a status request or cancellation targets the existing
run. No scheduled task or status-polling loop is needed.

## Runtime integrations

`await generate(args, ctx)` retains its existing result shape. CLI callers start
one child process and handle its exit; MCP, browser and web clients await their
existing tool-call response. Run these calls inside the host's background worker
when the host must remain interactive. Do not detach a coroutine from a CLI
process that exits, or assume an MCP server can wake a closed host conversation.

Embedded Python hosts can subscribe to the same run before it starts:

```python
from contextlib import aclosing
from pathlib import Path

from papervizagent.ops import GenerateInput, generate_events
from papervizagent.toolfactory import Context

async def render_in_background(data, deliver):
    args = GenerateInput(data=data)
    ctx = Context(config={}, data_dir=Path("outputs/figures").resolve())
    async with aclosing(generate_events(args, ctx)) as events:
        async for event in events:
            if event["type"] == "run.completed":
                await deliver(event["result"])
```

The application owns and retains the task running this coroutine. It may instead
call `await generate(args, ctx, on_event=handle_event)` with an async callback.
The callback runs in sequence and should return promptly; a callback failure is
propagated to the owner. The iterator waits on a queue for pushed events, without
a timer. Exiting its `aclosing` scope cancels and joins unfinished work. An
exception from the run is re-raised after its failure event. The owner should
handle that exception and deliver one failure report, not duplicate messages for
every role/candidate/run failure event.

Events carry `type`, `run_id`, `sequence`, and UTC `timestamp`:

| Event | Additional fields |
|---|---|
| `run.started` | `run_dir`, `num_candidates` |
| `candidate.started` | `candidate_id` |
| `role.started`, `role.completed` | `candidate_id`, `call_id`, `role`, `modality` |
| `role.failed`, `role.cancelled` | Same correlation fields; failures add `error_type` |
| `candidate.completed` | `candidate_id`, `artifact`, `result`, `critic_stop_reason`, `status` |
| `candidate.failed`, `candidate.cancelled` | `candidate_id`; failures add `error_type` |
| `run.completed` | `result` (the ordinary generate result), `status` |
| `run.failed`, `run.cancelled` | `trace`; failures add `error_type` |

`call_id` identifies the observed role invocation; it is not a provider request
ID. Actual provider/thread IDs remain in the saved trace. Events exclude model
prompts, image bytes, credentials, provider responses and raw exception text.
They expose local artifact paths and should stay within the caller's chosen host.
`role.completed` means the model request returned, not that its result passed
Critic validation. `run.completed` means the pipeline returned its result; inspect
candidate status and `critic_stop_reason` for partial results or `round_limit`.
Visual review is still required before presenting a figure as the selected output.

This is a live subscription, not a durable job service. The process and transport
must remain alive. After a disconnect or restart, inspect saved artifacts once
and resume deliberately; reconnecting must not silently start another paid run.
