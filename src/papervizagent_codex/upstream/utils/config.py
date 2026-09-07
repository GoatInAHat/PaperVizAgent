# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified by PaperVizAgent-codex to use a host-supplied backend and bounded local resources.

"""
Configuration for experiments
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class ExpConfig:
    """Experiment configuration"""

    dataset_name: Literal["PaperBananaBench"]
    task_name: Literal["diagram", "plot"] = "diagram"
    split_name: str = "test"
    temperature: float = 1.0
    exp_mode: str = ""
    retrieval_setting: Literal["auto", "manual", "random", "none"] = "auto"
    max_critic_rounds: int = 3
    plot_timeout_seconds: float = 30
    model_name: str = ""
    image_model_name: str = ""
    work_dir: Path = Path(__file__).parent.parent
    backend: Any = None

    timestamp: str | None = None

    def __post_init__(self):
        if self.backend is None:
            raise ValueError("ExpConfig.backend is required")
        self.timestamp = (
            time.strftime("%m%d_%H%M") if self.timestamp is None else self.timestamp
        )
        self.exp_name = f"{self.timestamp}_{self.retrieval_setting}ret_{self.exp_mode}_{self.split_name}"

        # mkdir result_dir if not exists
        self.result_dir = self.work_dir / "results" / f"{self.dataset_name}_{self.task_name}"
        self.result_dir.mkdir(exist_ok=True, parents=True)

    def resource_path(self, *parts: str) -> Path:
        """Prefer caller-provided resources, then the vendored pinned resources."""
        local = self.work_dir.joinpath(*parts)
        if local.exists():
            return local
        return Path(__file__).parent.parent.joinpath(*parts)
