import base64
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from papervizagent_codex import run_pipeline
from papervizagent_codex.upstream.utils.inference import normalize_contents, text_modality
from papervizagent_codex.upstream.utils.plot_execution import execute_plot_code


def png_base64() -> str:
    stream = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(stream, "PNG")
    return base64.b64encode(stream.getvalue()).decode()


class ScriptedBackend:
    def __init__(self, revisions=0, invalid_critic=False):
        self.calls = []
        self.revisions = revisions
        self.invalid_critic = invalid_critic
        self.critic_calls = 0

    async def generate(self, role, modality, system, contents, options):
        self.calls.append({"role": role, "modality": modality, "contents": contents, "options": options})
        if modality == "image":
            return [png_base64()]
        if role == "planner":
            return ["planner description"]
        if role == "stylist":
            return ["styled planner description"]
        if role == "critic":
            self.critic_calls += 1
            if self.invalid_critic:
                return ["not json"]
            if self.critic_calls <= self.revisions:
                return [json.dumps({
                    "critic_suggestions": f"revision {self.critic_calls}",
                    "revised_description": f"revised description {self.critic_calls}",
                })]
            return [json.dumps({
                "critic_suggestions": "No changes needed.",
                "revised_description": "No changes needed.",
            })]
        raise AssertionError((role, modality))


class PipelineContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_full_pipeline_preserves_role_handoffs_and_retrieval_none(self):
        backend = ScriptedBackend(revisions=1)
        with tempfile.TemporaryDirectory() as directory:
            result = await run_pipeline(
                backend,
                {"content": "method", "visual_intent": "caption"},
                work_dir=directory,
                retrieval_setting="none",
                max_critic_rounds=3,
            )
        self.assertEqual(result["top10_references"], [])
        self.assertEqual(result["retrieved_examples"], [])
        self.assertEqual(result["eval_image_field"], "target_diagram_critic_desc0_base64_jpg")
        self.assertEqual(
            [(call["role"], call["modality"]) for call in backend.calls],
            [("planner", "llm"), ("stylist", "llm"), ("visualizer", "image"),
             ("visualizer", "image"), ("critic", "vlm"), ("visualizer", "image"),
             ("critic", "vlm")],
        )
        critic_call = next(call for call in backend.calls if call["role"] == "critic")
        image = next(item for item in critic_call["contents"] if item["type"] == "image")
        self.assertEqual(image["source"]["type"], "base64")
        self.assertEqual(image["source"]["media_type"], "image/jpeg")

    async def test_more_than_three_critic_rounds_are_executed(self):
        backend = ScriptedBackend(revisions=4)
        with tempfile.TemporaryDirectory() as directory:
            result = await run_pipeline(
                backend,
                {"content": "method", "visual_intent": "caption"},
                work_dir=directory,
                max_critic_rounds=4,
            )
        self.assertEqual(backend.critic_calls, 4)
        self.assertIn("target_diagram_critic_desc3_base64_jpg", result)
        self.assertEqual(result["eval_image_field"], "target_diagram_critic_desc3_base64_jpg")

    async def test_invalid_critic_response_stops_without_rendering_bogus_revision(self):
        backend = ScriptedBackend(invalid_critic=True)
        with tempfile.TemporaryDirectory() as directory:
            result = await run_pipeline(
                backend,
                {"content": "method", "visual_intent": "caption"},
                work_dir=directory,
                max_critic_rounds=3,
            )
        self.assertEqual(result["critic_stop_reason"], "invalid_response")
        self.assertIn("target_diagram_critic_error0", result)
        self.assertEqual(result["eval_image_field"], "target_diagram_stylist_desc0_base64_jpg")
        self.assertEqual(sum(call["modality"] == "image" for call in backend.calls), 2)

    def test_image_normalization_controls_text_modality(self):
        contents = normalize_contents([{"type": "image", "image_base64": "abc"}])
        self.assertEqual(contents, [{"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": "abc"
        }}])
        self.assertEqual(text_modality(contents), "vlm")
        self.assertEqual(text_modality([{"type": "text", "text": "hello"}]), "llm")

    def test_plot_code_runs_in_bounded_child_process(self):
        if importlib.util.find_spec("matplotlib") is None:
            self.skipTest("matplotlib is supplied by the runtime package")
        rendered = execute_plot_code(
            "import matplotlib.pyplot as plt\nprint('child log')\nplt.plot([1, 2], [3, 4])",
            timeout_seconds=10,
        )
        self.assertGreater(len(rendered), 100)


if __name__ == "__main__":
    unittest.main()
