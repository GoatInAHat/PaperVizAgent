"""One optional configuration file, shared by every distribution surface."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr

Modality = Literal['llm', 'vlm', 'image']
Role = Literal['retriever', 'planner', 'stylist', 'visualizer', 'critic', 'vanilla', 'polish']
Provider = Literal['native', 'codex', 'gemini', 'openai', 'anthropic']


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    provider: Provider | None = None
    model: str | None = None
    api_key_env: str | None = None
    api_key: SecretStr | None = Field(default=None, exclude=True)
    base_url: str | None = None
    vertexai: bool = False
    project: str | None = None
    location: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class CodexAuth(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    access_token_env: str = 'CODEX_OAUTH_TOKEN'
    account_id_env: str = 'CODEX_ACCOUNT_ID'
    token_file: str | None = None
    codex_bin: str | None = None
    timeout: float = Field(default=600, gt=0)
    config: dict[str, Any] = Field(default_factory=dict)


class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    models: dict[Modality, Model] = Field(default_factory=dict)
    roles: dict[Role, Model] = Field(default_factory=dict)
    codex: CodexAuth = Field(default_factory=CodexAuth)
    pipeline: dict[str, Any] = Field(default_factory=dict)

    def resolve(self, role: str, modality: str, native: tuple[str, ...] = ()) -> Model:
        """Role override > modality override > available host capability > Codex."""
        values: dict[str, Any] = {}
        for spec in (self.models.get(modality), self.roles.get(role)):
            if spec is not None:
                incoming = spec.model_dump(exclude_unset=True)
                if spec.api_key is not None:
                    incoming['api_key'] = spec.api_key
                incoming['options'] = {**values.get('options', {}), **incoming.get('options', {})}
                values.update(incoming)
        if not values:
            return Model(provider='native' if modality in native else 'codex')
        values['provider'] = values.get('provider') or ('native' if modality in native and not values.get('model') else 'codex')
        return Model.model_validate(values)


def load_settings(path: str | None = None) -> Settings:
    """Read only an explicitly selected file; never search for credentials."""
    selected = path or os.environ.get('PAPERVIZAGENT_CONFIG')
    if not selected:
        return Settings()
    filename = Path(selected).expanduser().resolve()
    value = yaml.safe_load(filename.read_text()) or {}
    # Accept upstream's model_config.yaml as well as the portable per-role format.
    if any(key in value for key in ('defaults', 'api_keys', 'google_cloud', 'anthropic')):
        value = _upstream_config(value)
    settings = Settings.model_validate(value)
    if settings.codex.token_file:
        token_path = Path(settings.codex.token_file).expanduser()
        if not token_path.is_absolute():
            settings.codex.token_file = str(filename.parent / token_path)
    return settings


def _upstream_config(value: dict) -> dict:
    defaults = value.get('defaults', {})
    cloud = value.get('google_cloud', {})
    keys = value.get('api_keys', {})
    models = {}
    for modality, key in [('llm', 'model_name'), ('vlm', 'model_name'), ('image', 'image_model_name')]:
        name = defaults.get(key)
        if name:
            spec = {'provider': 'openai' if modality == 'image' and 'gpt-image' in name else 'gemini', 'model': name}
            if spec['provider'] == 'gemini' and cloud.get('project_id'):
                spec.update(vertexai=True, project=cloud['project_id'], location=cloud.get('location', 'global'))
            secret = keys.get('openai_api_key' if spec['provider'] == 'openai' else 'google_api_key')
            if secret:
                spec['api_key'] = secret
            models[modality] = spec
    return {**{key: value[key] for key in ('roles', 'codex', 'pipeline') if key in value},
            'models': {**models, **value.get('models', {})}}
