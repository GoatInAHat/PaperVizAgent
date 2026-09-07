"""Provider SDK boundary tests using local transports and official request types."""

import base64
import json
import os
import types
import unittest
from unittest.mock import patch

import anthropic
import httpx
import httpx2
import openai
from pydantic import SecretStr

from papervizagent.backends import provider_generate
from papervizagent.config import Model


TEXT = [{"type": "text", "text": "method details"}]
IMAGE_BYTES = b"portable-image"
IMAGE = [{"type": "image", "source": {
    "type": "base64", "media_type": "image/png", "data": base64.b64encode(IMAGE_BYTES).decode()
}}]


class ProviderRequestTest(unittest.IsolatedAsyncioTestCase):
    async def test_openai_text_uses_env_key_and_serializes_vision_and_output_limit(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(200, json={
                "id": "chat-request", "object": "chat.completion", "created": 0, "model": "gpt-test",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "review"}, "finish_reason": "stop"}],
            })

        original = openai.AsyncOpenAI

        def client(**kwargs):
            return original(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), max_retries=0)

        spec = Model(provider="openai", model="gpt-test", api_key=SecretStr("inline-key"), api_key_env="TEST_OPENAI_KEY")
        with patch.dict(os.environ, {"TEST_OPENAI_KEY": "environment-key"}, clear=True), patch.object(openai, "AsyncOpenAI", client):
            result = await provider_generate(spec, "vlm", "system instruction", TEXT + IMAGE, {"max_output_tokens": 77})

        self.assertEqual(result, ["review"])
        self.assertEqual(requests[0].headers["authorization"], "Bearer environment-key")
        self.assertEqual(requests[0].url.path, "/v1/chat/completions")
        payload = json.loads(requests[0].content)
        self.assertEqual(payload["max_completion_tokens"], 77)
        self.assertEqual(payload["messages"][0], {"role": "system", "content": "system instruction"})
        image_url = payload["messages"][1]["content"][1]["image_url"]["url"]
        self.assertEqual(image_url, f"data:image/png;base64,{base64.b64encode(IMAGE_BYTES).decode()}")

    async def test_openai_image_generate_and_explicit_edit_use_distinct_sdk_requests(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(200, json={"created": 0, "data": [{"b64_json": "generated"}]})

        original = openai.AsyncOpenAI

        def client(**kwargs):
            return original(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), max_retries=0)

        spec = Model(provider="openai", model="gpt-image-test", api_key=SecretStr("inline-key"))
        with patch.dict(os.environ, {}, clear=True), patch.object(openai, "AsyncOpenAI", client):
            generated = await provider_generate(spec, "image", "draw", TEXT, {
                "size": "1024x1024", "quality": "medium", "max_output_tokens": 99,
            })
            edited = await provider_generate(spec, "image", "revise", TEXT + IMAGE, {"edit": True})

        self.assertEqual((generated, edited), (["generated"], ["generated"]))
        generate, edit = requests
        self.assertEqual(generate.headers["authorization"], "Bearer inline-key")
        self.assertEqual(generate.url.path, "/v1/images/generations")
        generated_payload = json.loads(generate.content)
        self.assertEqual(generated_payload["size"], "1024x1024")
        self.assertEqual(generated_payload["quality"], "medium")
        self.assertNotIn("max_output_tokens", generated_payload)
        self.assertEqual(edit.url.path, "/v1/images/edits")
        self.assertIn("multipart/form-data", edit.headers["content-type"])
        self.assertIn(IMAGE_BYTES, edit.content)
        self.assertIn(b'name="image[]"', edit.content)

    async def test_anthropic_serializes_text_and_base64_image_with_env_key_precedence(self):
        requests = []

        async def handler(request):
            requests.append(request)
            return httpx2.Response(200, json={
                "id": "msg-request", "type": "message", "role": "assistant", "model": "claude-test",
                "content": [{"type": "text", "text": "analysis"}], "stop_reason": "end_turn",
                "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1},
            })

        original = anthropic.AsyncAnthropic

        def client(**kwargs):
            return original(**kwargs, http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)), max_retries=0)

        spec = Model(provider="anthropic", model="claude-test", api_key=SecretStr("inline-key"), api_key_env="TEST_ANTHROPIC_KEY")
        with patch.dict(os.environ, {"TEST_ANTHROPIC_KEY": "environment-key"}, clear=True), patch.object(anthropic, "AsyncAnthropic", client):
            result = await provider_generate(spec, "vlm", "inspect", TEXT + IMAGE, {"max_output_tokens": 31})

        self.assertEqual(result, ["analysis"])
        request = requests[0]
        self.assertEqual(request.headers["x-api-key"], "environment-key")
        self.assertEqual(request.url.path, "/v1/messages")
        payload = json.loads(request.content)
        self.assertEqual(payload["max_tokens"], 31)
        image = payload["messages"][0]["content"][1]
        self.assertEqual(image["type"], "image")
        self.assertEqual(image["source"], IMAGE[0]["source"])

    async def test_gemini_uses_official_parts_and_config_for_text_and_image(self):
        from google import genai

        captured = {}

        class Models:
            async def generate_content(self, **kwargs):
                captured.update(kwargs)
                return types.SimpleNamespace(candidates=[types.SimpleNamespace(content=types.SimpleNamespace(parts=[
                    types.SimpleNamespace(text="gemini answer", inline_data=None),
                    types.SimpleNamespace(text=None, inline_data=types.SimpleNamespace(data=b"gemini-image")),
                ]))])

        class AsyncClient:
            models = Models()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

        class Client:
            def __init__(self, **kwargs):
                captured["client_args"] = kwargs
                self.aio = AsyncClient()

        spec = Model(provider="gemini", model="gemini-test", api_key=SecretStr("inline-key"), api_key_env="TEST_GEMINI_KEY")
        with patch.dict(os.environ, {"TEST_GEMINI_KEY": "environment-key"}, clear=True), patch.object(genai, "Client", Client):
            text = await provider_generate(spec, "vlm", "inspect", TEXT + IMAGE, {"candidate_count": 2})
            image = await provider_generate(spec, "image", "draw", TEXT + IMAGE, {"aspect_ratio": "16:9", "image_size": "1K"})

        self.assertEqual(text, ["gemini answer"])
        self.assertEqual(image, [base64.b64encode(b"gemini-image").decode()])
        self.assertEqual(captured["client_args"]["api_key"], "environment-key")
        self.assertEqual(captured["model"], "gemini-test")
        config = captured["config"].model_dump(exclude_none=True)
        self.assertEqual(config["system_instruction"], "draw")
        self.assertEqual(config["response_modalities"], ["IMAGE"])
        self.assertEqual(config["image_config"], {"aspect_ratio": "16:9", "image_size": "1K"})
        parts = captured["contents"]
        self.assertEqual(parts[0].text, "method details")
        self.assertEqual(parts[1].inline_data.mime_type, "image/png")
        self.assertEqual(parts[1].inline_data.data, IMAGE_BYTES)


if __name__ == "__main__":
    unittest.main()
