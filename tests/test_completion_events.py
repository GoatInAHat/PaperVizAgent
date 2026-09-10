"""Runs push completion once, preserve errors, and stop when their owner closes."""
import asyncio
import base64
from contextlib import aclosing
from io import BytesIO
from pathlib import Path

from PIL import Image
import pytest

from papervizagent import ops, pipeline
from papervizagent.toolfactory import Context


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    image = BytesIO()
    Image.new('RGB', (2, 2), 'blue').save(image, format='JPEG')
    encoded = base64.b64encode(image.getvalue()).decode()

    class Backend:
        trace = []
        closed = False

        def __init__(self, _settings):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            Backend.closed = True

        async def generate(self, *_args):
            return [encoded]

    async def run(backend, data, **_options):
        image, = await backend.generate('visualizer', 'image', 'private prompt', [], {})
        return {'eval_image_field': 'image', 'image': image,
                'critic_stop_reason': data.get('stop', 'round_limit')}

    monkeypatch.setattr(ops, 'Backend', Backend)
    monkeypatch.setattr(pipeline, 'run_pipeline', run)
    return Context(config={}, data_dir=tmp_path), Backend


async def test_stream_completes_once_after_artifacts_and_keeps_candidates_distinct(runtime):
    ctx, backend = runtime
    args = ops.GenerateInput(data={}, num_candidates=2)
    events = [event async for event in ops.generate_events(args, ctx)]
    assert events[0]['type'] == 'run.started'
    assert events[-1]['type'] == 'run.completed'
    assert [e['type'] for e in events].count('run.completed') == 1
    assert [e['sequence'] for e in events] == list(range(1, len(events) + 1))
    assert len({e['run_id'] for e in events}) == 1
    starts = [e for e in events if e['type'] == 'role.started']
    ends = [e for e in events if e['type'] == 'role.completed']
    assert {e['candidate_id'] for e in starts} == {0, 1}
    assert {e['call_id'] for e in starts} == {e['call_id'] for e in ends}
    assert len({e['call_id'] for e in starts}) == 2
    result = events[-1]['result']
    assert Path(result['trace']).exists()
    assert backend.closed
    for candidate in result['candidates']:
        assert Path(candidate['artifact']).exists()
        assert Path(candidate['result']).exists()
        assert candidate['critic_stop_reason'] == 'round_limit'
    assert 'private prompt' not in str(events)


async def test_partial_pipeline_is_not_approval(runtime):
    ctx, _ = runtime
    events = [e async for e in ops.generate_events(
        ops.GenerateInput(data={'stop': 'invalid_response'}), ctx)]
    assert events[-1]['type'] == 'run.completed'
    assert events[-1]['status'] == 'partial'
    assert events[-1]['result']['candidates'][0]['critic_stop_reason'] == 'invalid_response'


async def test_queued_candidate_is_not_reported_started(runtime, monkeypatch):
    ctx, backend = runtime
    entered, release = asyncio.Event(), asyncio.Event()
    original = backend.generate
    events = []

    async def wait(self, *args):
        entered.set()
        await release.wait()
        return await original(self, *args)

    async def receive(event):
        events.append(event)

    monkeypatch.setattr(backend, 'generate', wait)
    task = asyncio.create_task(ops.generate(
        ops.GenerateInput(data={}, num_candidates=2, max_concurrent=1), ctx, on_event=receive))
    try:
        await entered.wait()
        assert [e['candidate_id'] for e in events if e['type'] == 'candidate.started'] == [0]
    finally:
        release.set()
        await task
    assert [e['candidate_id'] for e in events if e['type'] == 'candidate.started'] == [0, 1]


async def test_failure_is_pushed_then_raised_without_leaking_error_body(runtime, monkeypatch):
    ctx, backend = runtime

    async def fail(*_args):
        raise RuntimeError('private-provider-response')

    monkeypatch.setattr(backend, 'generate', fail)
    events = []
    with pytest.raises(RuntimeError, match='private-provider-response'):
        async for event in ops.generate_events(ops.GenerateInput(data={}), ctx):
            events.append(event)
    assert [e['type'] for e in events][-3:] == ['role.failed', 'candidate.failed', 'run.failed']
    assert 'private-provider-response' not in str(events)
    assert backend.closed
    assert Path(events[-1]['trace']).is_file()


async def test_closing_stream_joins_cancelled_work(runtime, monkeypatch):
    ctx, backend = runtime
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def wait(*_args):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(backend, 'generate', wait)
    async with aclosing(ops.generate_events(ops.GenerateInput(data={}), ctx)) as events:
        async for event in events:
            if event['type'] == 'role.started':
                await entered.wait()
                break
    assert cancelled.is_set()
    assert backend.closed


async def test_callback_is_attached_before_run_and_receives_cancellation(runtime, monkeypatch):
    ctx, backend = runtime
    entered = asyncio.Event()
    events = []

    async def wait(*_args):
        entered.set()
        await asyncio.Event().wait()

    async def receive(event):
        events.append(event)

    monkeypatch.setattr(backend, 'generate', wait)
    task = asyncio.create_task(ops.generate(ops.GenerateInput(data={}), ctx, on_event=receive))
    await entered.wait()
    assert events[0]['type'] == 'run.started'
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert [e['type'] for e in events][-3:] == ['role.cancelled', 'candidate.cancelled', 'run.cancelled']
    assert backend.closed
