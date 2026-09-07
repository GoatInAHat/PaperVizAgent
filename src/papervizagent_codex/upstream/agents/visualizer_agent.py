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
Vanilla Agent - Directly rendering images based on the method section.
"""

from typing import Dict, Any
import asyncio

from ..utils.logging import stderr_print as _stderr_print
from ..utils import image_utils
from ..utils.inference import generate_image, generate_text
from ..utils.plot_execution import execute_plot_code
from .base_agent import BaseAgent


class VisualizerAgent(BaseAgent):
    """Visualizer Agent to generate images based on user queries"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Task-specific configurations
        if "plot" in self.exp_config.task_name:
            self.model_name = self.exp_config.model_name
            self.system_prompt = PLOT_VISUALIZER_AGENT_SYSTEM_PROMPT
            self.process_executor = None
            self.task_config = {
                "task_name": "plot",
                "use_image_generation": False,  # Use code generation instead
                "prompt_template": "Use python matplotlib to generate a statistical plot based on the following detailed description: {desc}\n Only provide the code without any explanations. Code:",
                "max_output_tokens": 50000,
            }
            # The code below is for applying image generation models to statistics plots:
            # self.model_name = self.exp_config.image_model_name
            # self.system_prompt = """You are an expert statistical plot illustrator. Generate high-quality statistical plots based on user requests. Note that you should not use code, but directly generate the image."""
            # self.process_executor = None
            # self.task_config = {
            #     "task_name": "plot",
            #     "use_image_generation": True,  # Use direct image generation
            #     "prompt_template": "Render an image based on the following description: {desc}\n Plot:",
            #     "max_output_tokens": 50000,
            # }

        else:
            self.model_name = self.exp_config.image_model_name
            self.system_prompt = DIAGRAM_VISUALIZER_AGENT_SYSTEM_PROMPT
            self.process_executor = None  # Not needed for diagrams
            self.task_config = {
                "task_name": "diagram",
                "use_image_generation": True,  # Use direct image generation
                "prompt_template": "Render an image based on the following detailed description: {desc}\n Note that do not include figure titles in the image. Diagram: ",
                "max_output_tokens": 50000,
            }

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified processing method that works for both diagram and plot tasks.
        Uses task_config to determine task-specific parameters.
        """
        cfg = self.task_config
        task_name = cfg["task_name"]
        
        desc_keys_to_process = []
        for key in [
            f"target_{task_name}_desc0",
            f"target_{task_name}_stylist_desc0",
        ]:
            if key in data and f"{key}_base64_jpg" not in data:
                desc_keys_to_process.append(key)
        
        critic_rounds = max(
            self.exp_config.max_critic_rounds,
            int(data.get("max_critic_rounds", 0)),
            int(data.get("current_critic_round", -1)) + 1,
        )
        for round_idx in range(critic_rounds):
            key = f"target_{task_name}_critic_desc{round_idx}"
            if key in data and f"{key}_base64_jpg" not in data:
                critic_suggestions_key = f"target_{task_name}_critic_suggestions{round_idx}"
                critic_suggestions = data.get(critic_suggestions_key, "")
                
                if critic_suggestions.strip() == "No changes needed." and round_idx > 0:
                    # Reuse previous round's base64
                    prev_base64_key = f"target_{task_name}_critic_desc{round_idx - 1}_base64_jpg"
                    if prev_base64_key in data:
                        data[f"{key}_base64_jpg"] = data[prev_base64_key]
                        _stderr_print(f"[Visualizer] Reused base64 from round {round_idx - 1} for {key}")
                        continue
                
                desc_keys_to_process.append(key)
        
        for desc_key in desc_keys_to_process:
            prompt_text = cfg["prompt_template"].format(desc=data[desc_key])
            content_list = [{"type": "text", "text": prompt_text}]
            
            if cfg["use_image_generation"]:
                response_list = await generate_image(
                    self.exp_config.backend,
                    role="visualizer",
                    system=self.system_prompt,
                    contents=content_list,
                    temperature=self.exp_config.temperature,
                    aspect_ratio=data.get("additional_info", {}).get("rounded_ratio", "1:1"),
                )
            else:
                response_list = await generate_text(
                    self.exp_config.backend,
                    role="visualizer",
                    system=self.system_prompt,
                    contents=content_list,
                    temperature=self.exp_config.temperature,
                    max_output_tokens=cfg["max_output_tokens"],
                )
            
            if not response_list or not response_list[0]:
                continue
            
            # Post-process based on task type
            if cfg["use_image_generation"]:
                # Convert PNG to JPG
                converted_jpg = await asyncio.to_thread(
                    image_utils.convert_png_b64_to_jpg_b64, response_list[0]
                )
                if converted_jpg:
                    data[f"{desc_key}_base64_jpg"] = converted_jpg
                else:
                    _stderr_print(f"⚠️  Skipping {desc_key}: image conversion failed")
            else:
                # Plot: execute generated code
                raw_code = response_list[0]
                
                data[f"{desc_key}_code"] = raw_code
                try:
                    base64_jpg = await asyncio.to_thread(
                        execute_plot_code,
                        raw_code,
                        self.exp_config.plot_timeout_seconds,
                        self.exp_config.plot_dpi,
                    )
                except (RuntimeError, TimeoutError) as error:
                    data[f"{desc_key}_plot_error"] = str(error)
                else:
                    if base64_jpg:
                        data[f"{desc_key}_base64_jpg"] = base64_jpg
        
        return data


DIAGRAM_VISUALIZER_AGENT_SYSTEM_PROMPT = """You are an expert scientific diagram illustrator. Generate high-quality scientific diagrams based on user requests."""

PLOT_VISUALIZER_AGENT_SYSTEM_PROMPT = """You are an expert statistical plot illustrator. Write code to generate high-quality statistical plots based on user requests."""


# !!! Note: If using image generation models, use the following system prompt instead:

# PLOT_VISUALIZER_AGENT_SYSTEM_PROMPT = """You are an expert statistical plot illustrator. Generate high-quality statistical plots based on user requests. Note that you should not use code, but directly generate the image."""
