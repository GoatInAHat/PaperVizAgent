# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Module-local logging that preserves stdout for protocol traffic."""

import builtins
import sys
from typing import Any


def stderr_print(*args: Any, **kwargs: Any) -> None:
    kwargs.setdefault("file", sys.stderr)
    builtins.print(*args, **kwargs)
