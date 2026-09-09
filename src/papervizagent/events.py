"""In-process lifecycle notifications; the caller owns the task and transport."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .upstream.utils.inference import InferenceBackend

EventSink = Callable[[dict[str, Any]], Awaitable[None]]


class RunEvents:
    def __init__(self, run_id: str, sink: EventSink | None):
        self.run_id = run_id
        self.sink = sink
        self.sequence = 0
        self._lock = asyncio.Lock()

    async def emit(self, event_type: str, **fields: Any) -> None:
        if self.sink is None:
            return
        async with self._lock:
            self.sequence += 1
            await self.sink({
                'type': event_type, 'run_id': self.run_id,
                'sequence': self.sequence,
                'timestamp': datetime.now(timezone.utc).isoformat(), **fields,
            })


class ObservedBackend:
    """Observe actual model calls without changing upstream roles or routing."""
    def __init__(self, backend: InferenceBackend, events: RunEvents, candidate_id: int):
        self.backend = backend
        self.events = events
        self.candidate_id = candidate_id

    async def generate(self, role, modality, system, contents, options):
        call = {'candidate_id': self.candidate_id, 'call_id': str(uuid4()),
                'role': role, 'modality': modality}
        await self.events.emit('role.started', **call)
        try:
            result = await self.backend.generate(role, modality, system, contents, options)
        except asyncio.CancelledError:
            await self.events.emit('role.cancelled', **call)
            raise
        except Exception as error:
            # Provider errors can contain request bodies or credentials. Only the
            # exception type crosses the notification boundary.
            await self.events.emit('role.failed', **call, error_type=type(error).__name__)
            raise
        await self.events.emit('role.completed', **call)
        return result
