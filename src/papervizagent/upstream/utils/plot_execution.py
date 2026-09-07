# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Adapted for PaperVizAgent: bound generated-code execution in a child process.

"""Bounded plot-code execution.

The child process limits hangs and keeps plotting globals out of the coordinator.
It is not a security sandbox; callers must apply their own sandbox when
untrusted model output requires a security boundary.
"""

import multiprocessing
import os
import re
import sys
import tempfile
from typing import Any


def _worker(code_text: str, dpi: int, connection: Any) -> None:
    try:
        # This assignment is child-process-local and keeps MCP stdout clean.
        sys.stdout = sys.stderr
        import base64
        import io
        import matplotlib.pyplot as plt

        with tempfile.TemporaryDirectory(prefix="paperviz-plot-") as directory:
            os.chdir(directory)
            match = re.search(r"```python(.*?)```", code_text, re.DOTALL)
            code = match.group(1).strip() if match else code_text.strip()
            plt.switch_backend("Agg")
            plt.close("all")
            plt.rcdefaults()
            namespace: dict[str, Any] = {}
            exec(code, namespace)
            if not plt.get_fignums():
                connection.send(None)
                return
            buffer = io.BytesIO()
            plt.savefig(buffer, format="jpeg", bbox_inches="tight", dpi=dpi)
            connection.send(base64.b64encode(buffer.getvalue()).decode("utf-8"))
    except BaseException as error:
        connection.send({"error": f"{type(error).__name__}: {error}"})
    finally:
        connection.close()


def _stop(process: multiprocessing.Process) -> None:
    if not process.is_alive():
        return
    process.terminate()
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join(5)


def execute_plot_code(
    code_text: str, timeout_seconds: float = 30, dpi: int = 300
) -> str | None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    process = multiprocessing.get_context("spawn").Process(
        target=_worker, args=(code_text, dpi, sender)
    )
    process.start()
    sender.close()
    if not receiver.poll(timeout_seconds):
        _stop(process)
        receiver.close()
        raise TimeoutError(f"plot execution exceeded {timeout_seconds:g} seconds")
    try:
        result = receiver.recv()
    except EOFError as error:
        process.join(5)
        receiver.close()
        raise RuntimeError("plot worker exited without a result") from error
    process.join(5)
    _stop(process)
    receiver.close()
    if isinstance(result, dict):
        raise RuntimeError(result["error"])
    return result
