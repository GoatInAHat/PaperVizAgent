"""Network-free routing contracts for the portable inference adapters."""

import asyncio
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, patch

from papervizagent_codex.backends import Backend, token_credentials
from papervizagent_codex.config import Model, Settings, load_settings


class RoutingTest(unittest.IsolatedAsyncioTestCase):
    def test_explicit_routes_win_over_available_native_capability(self):
        settings = Settings(
            models={"llm": Model(provider="gemini", model="shared")},
            roles={"critic": Model(provider="anthropic", model="reviewer")},
        )

        self.assertEqual(settings.resolve("planner", "llm", ("llm",)).provider, "gemini")
        critic = settings.resolve("critic", "llm", ("llm",))
        self.assertEqual((critic.provider, critic.model), ("anthropic", "reviewer"))
        self.assertEqual(settings.resolve("visualizer", "image", ("image",)).provider, "native")
        self.assertEqual(settings.resolve("visualizer", "vlm", ("image",)).provider, "codex")

    async def test_native_callback_and_codex_fallback_are_selected_per_modality(self):
        received = []

        async def native(**request):
            received.append(request)
            return ["host answer"]

        backend = Backend(native={"llm": native})
        backend._codex_generate = AsyncMock(return_value=["codex answer"])
        text = [{"type": "text", "text": "paper"}]

        self.assertEqual(await backend.generate("planner", "llm", "plan", text), ["host answer"])
        self.assertEqual(await backend.generate("critic", "vlm", "inspect", text), ["codex answer"])
        self.assertEqual(received[0]["role"], "planner")
        self.assertEqual(received[0]["options"], {})
        backend._codex_generate.assert_awaited_once()
        self.assertEqual([entry["provider"] for entry in backend.trace], ["native"])

    def test_vision_model_selection_requires_image_input_and_honors_default(self):
        backend = Backend()
        backend.models = [
            {"id": "text", "model": "text-model", "inputModalities": ["text"], "isDefault": True},
            {"id": "vision", "model": "vision-model", "inputModalities": ["text", "image"], "isDefault": False},
            {"id": "vision-default", "model": "vision-default", "inputModalities": ["image"], "isDefault": True},
        ]

        self.assertEqual(backend.choose_model(Model(), "vlm"), "vision-default")
        self.assertEqual(backend.choose_model(Model(model="vision"), "vlm"), "vision")
        with self.assertRaisesRegex(ValueError, "unavailable for vlm"):
            backend.choose_model(Model(model="text"), "vlm")

    def test_oauth_env_jwt_and_token_file_are_read_only_and_not_logged(self):
        account = "acct-from-jwt"
        payload = base64.urlsafe_b64encode(json.dumps({
            "https://api.openai.com/auth": {"chatgpt_account_id": account}
        }).encode()).decode().rstrip("=")
        token = f"header.{payload}.signature"
        with patch.dict(os.environ, {"CODEX_OAUTH_TOKEN": token}, clear=True), self.assertNoLogs():
            self.assertEqual(token_credentials(Settings()), {
                "type": "chatgptAuthTokens", "accessToken": token, "chatgptAccountId": account
            })

        with tempfile.TemporaryDirectory() as directory:
            token_file = Path(directory) / "token.json"
            original = json.dumps({"accessToken": "file-token", "chatgptAccountId": "file-account"})
            token_file.write_text(original)
            settings = Settings.model_validate({"codex": {"token_file": str(token_file)}})
            with patch.dict(os.environ, {"CODEX_OAUTH_TOKEN": "different"}, clear=True), self.assertNoLogs():
                credentials = token_credentials(settings)
            self.assertEqual(credentials["accessToken"], "file-token")
            self.assertEqual(credentials["chatgptAccountId"], "file-account")
            self.assertEqual(token_file.read_text(), original)

    async def test_managed_codex_credentials_do_not_trigger_external_login(self):
        constructed = []

        class CodexConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Client:
            def __init__(self, config):
                self.config = config
                self.logins = []
                constructed.append(self)

            async def start(self):
                pass

            async def initialize(self):
                pass

            async def account_login_start(self, credentials):
                self.logins.append(credentials)

            async def account_read(self):
                return types.SimpleNamespace(account=types.SimpleNamespace(root=types.SimpleNamespace(type="chatgpt")))

            async def close(self):
                pass

        codex_module = types.ModuleType("openai_codex")
        codex_module.CodexConfig = CodexConfig
        async_client_module = types.ModuleType("openai_codex.async_client")
        async_client_module.AsyncCodexClient = Client
        with patch.dict(sys.modules, {
            "openai_codex": codex_module,
            "openai_codex.async_client": async_client_module,
        }), patch.dict(os.environ, {}, clear=True), patch.object(Backend, "_model_catalog", new=AsyncMock(return_value=[])):
            async with Backend() as backend:
                await backend.codex()
        self.assertEqual(len(constructed), 1)
        self.assertEqual(constructed[0].logins, [])

    def test_upstream_inline_key_stays_out_of_status_route_and_relative_token_file_resolves(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "model_config.yaml"
            config.write_text("""
defaults:
  model_name: gemini-2.5-pro
  image_model_name: gpt-image-1
api_keys:
  google_api_key: google-inline-secret
  openai_api_key: openai-inline-secret
codex:
  token_file: auth/token.json
""")
            settings = load_settings(str(config))

            routes = {
                modality: settings.resolve("visualizer", modality).model_dump(exclude_none=True)
                for modality in ("llm", "vlm", "image")
            }
            rendered = json.dumps(routes)
            self.assertNotIn("google-inline-secret", rendered)
            self.assertNotIn("openai-inline-secret", rendered)
            self.assertNotIn("api_key", rendered)
            self.assertEqual(settings.codex.token_file, str((config.parent / "auth/token.json").resolve()))
            self.assertEqual(settings.models["image"].api_key.get_secret_value(), "openai-inline-secret")

    async def test_codex_rejects_explicit_unsupported_option_before_starting_a_thread(self):
        backend = Backend()
        backend.models = [{"id": "coordinator", "model": "coordinator", "inputModalities": ["text"], "isDefault": True}]
        client = _TurnClient([])
        backend.client = client
        backend._directory = tempfile.TemporaryDirectory()
        capabilities = types.ModuleType("openai_codex.generated.v2_all")
        capabilities.ModelProviderCapabilitiesReadResponse = object
        try:
            with patch.dict(sys.modules, {"openai_codex.generated.v2_all": capabilities}):
                with self.assertRaisesRegex(ValueError, "temperature"):
                    await backend._codex_generate(Model(provider="codex", options={"temperature": 0.1}), "planner", "llm", "system", [{"type": "text", "text": "x"}], {"temperature": 0.1})
            self.assertEqual(client.thread_requests, [])
        finally:
            backend._directory.cleanup()

    async def test_codex_uses_a_fresh_thread_and_returns_generated_image(self):
        completed_image = types.SimpleNamespace(
            method="item/completed",
            payload=types.SimpleNamespace(item=types.SimpleNamespace(root=types.SimpleNamespace(
                type="imageGeneration", status="completed", result="generated-base64", saved_path=None
            ))),
        )
        completed_turn = types.SimpleNamespace(
            method="turn/completed",
            payload=types.SimpleNamespace(turn=types.SimpleNamespace(status=types.SimpleNamespace(value="completed"))),
        )
        backend = Backend()
        backend.models = [{"id": "coordinator", "model": "coordinator", "inputModalities": ["text"], "isDefault": True}]
        client = _TurnClient([completed_image, completed_turn, completed_image, completed_turn])
        backend.client = client
        backend._directory = tempfile.TemporaryDirectory()
        capabilities = types.ModuleType("openai_codex.generated.v2_all")
        capabilities.ModelProviderCapabilitiesReadResponse = object
        try:
            with patch.dict(sys.modules, {"openai_codex.generated.v2_all": capabilities}):
                first = await backend._codex_generate(Model(provider="codex"), "visualizer", "image", "draw", [{"type": "text", "text": "plot"}], {})
                second = await backend._codex_generate(Model(provider="codex"), "visualizer", "image", "draw", [{"type": "text", "text": "plot"}], {})
            self.assertEqual(first, ["generated-base64"])
            self.assertEqual(second, ["generated-base64"])
            self.assertEqual([request["ephemeral"] for request in client.thread_requests], [True, True])
            self.assertNotEqual(client.thread_requests[0]["_thread_id"], client.thread_requests[1]["_thread_id"])
            self.assertEqual(len(client.unregistered), 2)
        finally:
            backend._directory.cleanup()


class _TurnClient:
    def __init__(self, events):
        self.events = list(events)
        self.thread_requests = []
        self.unregistered = []
        self._threads = 0
        self._turns = 0

    async def request(self, *_args, **_kwargs):
        return types.SimpleNamespace(image_generation=True)

    async def thread_start(self, request):
        self._threads += 1
        request = dict(request)
        request["_thread_id"] = f"thread-{self._threads}"
        self.thread_requests.append(request)
        return types.SimpleNamespace(thread=types.SimpleNamespace(id=request["_thread_id"]))

    async def turn_start(self, _thread_id, _items, _params):
        self._turns += 1
        return types.SimpleNamespace(turn=types.SimpleNamespace(id=f"turn-{self._turns}"))

    async def next_turn_notification(self, _turn_id):
        return self.events.pop(0)

    async def turn_interrupt(self, *_args):
        raise AssertionError("successful turn should not be interrupted")

    def unregister_turn_notifications(self, turn_id):
        self.unregistered.append(turn_id)
