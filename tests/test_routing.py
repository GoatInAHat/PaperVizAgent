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

from papervizagent.backends import Backend, token_credentials
from papervizagent.config import Model, Settings, load_settings


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

    def test_unconfigured_routes_keep_every_verified_native_modality(self):
        settings = Settings()
        for modality in ("llm", "vlm", "image"):
            self.assertEqual(settings.resolve("visualizer", modality, ("llm", "vlm", "image")).provider, "native")

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
        self.assertEqual(backend.choose_model(Model(model="vision"), "vlm"), "vision-model")
        with self.assertRaisesRegex(ValueError, "unavailable for vlm"):
            backend.choose_model(Model(model="text"), "vlm")

    def test_balanced_policy_beats_an_expensive_server_default_without_model_name_heuristics(self):
        backend = Backend()
        backend.models = [
            {"id": "opaque-default", "model": "opaque-default", "description": "Most capable general model.", "inputModalities": ["text", "image"], "isDefault": True, "supportedReasoningEfforts": []},
            {"id": "future-name", "model": "future-model", "description": "Balanced general model for everyday work.", "inputModalities": ["text", "image"], "isDefault": False, "supportedReasoningEfforts": []},
        ]
        selected = backend.select_model(Model(), "llm")
        self.assertEqual((selected.model, selected.reason, selected.classification), ("future-model", "balanced_catalog_label", "balanced"))

    def test_quality_policy_prefers_advertised_general_quality_and_excludes_specialty_hidden_and_legacy(self):
        backend = Backend(Settings(model_policy="quality"))
        backend.models = [
            {"id": "old", "model": "old", "description": "Previous-generation flagship.", "inputModalities": ["text", "image"], "isDefault": True, "supportedReasoningEfforts": []},
            {"id": "cyber", "model": "cyber", "description": "Most capable frontier model.", "modelSpecialty": "cyber", "inputModalities": ["text", "image"], "isDefault": False, "supportedReasoningEfforts": []},
            {"id": "hidden", "model": "hidden", "description": "Most capable frontier model.", "hidden": True, "inputModalities": ["text", "image"], "isDefault": False, "supportedReasoningEfforts": []},
            {"id": "current", "model": "current", "description": "Flagship general model.", "inputModalities": ["text", "image"], "isDefault": False, "supportedReasoningEfforts": []},
        ]
        selected = backend.select_model(Model(), "vlm")
        self.assertEqual((selected.model, selected.reason), ("current", "quality_catalog_label"))

    def test_unknown_catalog_labels_fall_back_to_server_default_and_explicit_ids_are_canonicalized(self):
        backend = Backend()
        backend.models = [
            {"id": "retired", "model": "retired-model", "description": "Deprecated general model.", "inputModalities": ["text", "image"], "isDefault": True, "supportedReasoningEfforts": []},
            {"id": "new-id", "model": "canonical-new", "description": "General work.", "inputModalities": ["text", "image"], "isDefault": True, "supportedReasoningEfforts": []},
        ]
        selected = backend.select_model(Model(), "llm")
        self.assertEqual((selected.model, selected.reason), ("canonical-new", "server_default_fallback"))
        explicit = backend.select_model(Model(model="new-id"), "llm")
        self.assertEqual((explicit.model, explicit.reason), ("canonical-new", "explicit"))

    def test_explicit_model_can_use_hidden_or_specialized_catalog_entries_when_capable(self):
        backend = Backend()
        backend.models = [
            {"id": "hidden-specialist", "model": "hidden-specialist", "hidden": True,
             "modelSpecialty": "science", "inputModalities": ["text", "image"],
             "description": "Specialized model.", "isDefault": False},
            {"id": "text-only", "model": "text-only", "inputModalities": ["text"],
             "description": "General model.", "isDefault": True},
        ]
        self.assertEqual(backend.choose_model(Model(model="hidden-specialist"), "vlm"), "hidden-specialist")
        with self.assertRaisesRegex(ValueError, "unavailable for vlm"):
            backend.choose_model(Model(model="text-only"), "vlm")

    def test_quality_policy_uses_supported_effort_and_explicit_controls_validate_before_thread(self):
        backend = Backend(Settings(model_policy="quality"))
        backend.models = [{
            "id": "quality", "model": "quality", "description": "Flagship general model.",
            "inputModalities": ["text", "image"], "isDefault": True,
            "supportedReasoningEfforts": [{"reasoningEffort": "medium"}, {"reasoningEffort": "high"}],
            "serviceTiers": [{"id": "priority"}],
        }]
        selected = backend.select_model(Model(), "llm")
        from papervizagent.model_selection import automatic_effort, validate_controls
        self.assertEqual(automatic_effort(backend.models[0], policy="quality", modality="llm")[0], "high")
        with self.assertRaisesRegex(ValueError, "does not support effort"):
            validate_controls(backend.models[0], {"effort": "ultra"})
        with self.assertRaisesRegex(ValueError, "does not support service_tier"):
            validate_controls(backend.models[0], {"service_tier": "slow"})
        validate_controls(backend.models[0], {"effort": None, "service_tier": None})
        self.assertEqual(selected.model, "quality")

    async def test_catalog_selection_reason_and_policy_effort_are_recorded_on_codex_turn(self):
        completed_text = types.SimpleNamespace(
            method="item/completed",
            payload=types.SimpleNamespace(item=types.SimpleNamespace(root=types.SimpleNamespace(
                type="agentMessage", text="done"
            ))),
        )
        completed_turn = types.SimpleNamespace(
            method="turn/completed",
            payload=types.SimpleNamespace(turn=types.SimpleNamespace(status=types.SimpleNamespace(value="completed"))),
        )
        backend = Backend(Settings(model_policy="balanced"))
        backend.models = [{
            "id": "opaque", "model": "future-balanced", "description": "Balanced general model.",
            "inputModalities": ["text", "image"], "isDefault": False,
            "supportedReasoningEfforts": [{"reasoningEffort": "low"}, {"reasoningEffort": "medium"}],
            "serviceTiers": [],
        }]
        client = _TurnClient([completed_text, completed_turn, completed_text, completed_turn])
        backend.client = client
        backend._directory = tempfile.TemporaryDirectory()
        try:
            await backend._codex_generate(Model(provider="codex"), "planner", "llm", "system", [{"type": "text", "text": "x"}], {})
            self.assertEqual(client.turn_params, [{"effort": "medium"}])
            self.assertEqual(backend.trace[-1]["model"], "future-balanced")
            self.assertEqual(backend.trace[-1]["model_policy"], "balanced")
            self.assertEqual(backend.trace[-1]["effort"], "medium")
            self.assertEqual(backend.trace[-1]["model_selection_reason"], "balanced_catalog_label")
            await backend._codex_generate(Model(provider="codex", options={"effort": None, "service_tier": None}), "planner", "llm", "system", [{"type": "text", "text": "x"}], {"effort": None, "service_tier": None})
            self.assertEqual(client.turn_params[-1], {})
            self.assertIsNone(backend.trace[-1]["effort"])
            self.assertIsNone(backend.trace[-1]["service_tier"])
        finally:
            backend._directory.cleanup()

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
        self.turn_params = []
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
        self.turn_params.append(_params)
        return types.SimpleNamespace(turn=types.SimpleNamespace(id=f"turn-{self._turns}"))

    async def next_turn_notification(self, _turn_id):
        return self.events.pop(0)

    async def turn_interrupt(self, *_args):
        raise AssertionError("successful turn should not be interrupted")

    def unregister_turn_notifications(self, turn_id):
        self.unregistered.append(turn_id)


async def test_failed_terminal_event_is_not_interrupted_again(tmp_path):
    terminal = types.SimpleNamespace(method='turn/completed', payload=types.SimpleNamespace(
        turn=types.SimpleNamespace(status=types.SimpleNamespace(value='failed'))))
    backend = Backend()
    backend.models = [{'id': 'coordinator', 'model': 'coordinator', 'inputModalities': ['text']}]
    backend.client = _TurnClient([terminal])
    backend._directory = types.SimpleNamespace(name=str(tmp_path))
    with unittest.TestCase().assertRaisesRegex(RuntimeError, 'Codex inference failed'):
        await backend._codex_generate(Model(provider='codex'), 'planner', 'llm', 'system', [], {})
    assert backend.client.unregistered == ['turn-1']


async def test_cancellation_cleanup_cannot_mask_original_exception(tmp_path):
    import asyncio
    entered = asyncio.Event()

    class Client(_TurnClient):
        async def next_turn_notification(self, _turn_id):
            entered.set()
            await asyncio.Event().wait()

        async def turn_interrupt(self, *_args):
            raise RuntimeError('no active turn to interrupt')

    backend = Backend()
    backend.models = [{'id': 'coordinator', 'model': 'coordinator', 'inputModalities': ['text']}]
    backend.client = Client([])
    backend._directory = types.SimpleNamespace(name=str(tmp_path))
    task = asyncio.create_task(backend._codex_generate(
        Model(provider='codex'), 'planner', 'llm', 'system', [], {}))
    await entered.wait()
    task.cancel()
    with unittest.TestCase().assertRaises(asyncio.CancelledError):
        await task
    assert backend.client.unregistered == ['turn-1']
