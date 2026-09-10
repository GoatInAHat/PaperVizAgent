"""Provider-selected image formats survive the host handoff unchanged."""
import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image
import pytest

from papervizagent.ops import InferInput, infer
from papervizagent.toolfactory import Context


@pytest.mark.parametrize('format,suffix', [('PNG', '.png'), ('JPEG', '.jpg'), ('WEBP', '.webp')])
async def test_infer_preserves_provider_image_format(tmp_path, format, suffix):
    buffer = BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buffer, format=format)
    raw = buffer.getvalue()
    with patch('papervizagent.ops.Backend') as cls:
        backend = cls.return_value.__aenter__.return_value
        backend.trace = []
        backend.generate = AsyncMock(return_value=[base64.b64encode(raw).decode()])
        result = await infer(InferInput(role='visualizer', modality='image',
                                       contents=[{'type': 'text', 'text': 'red square'}]),
                             Context(config={}, data_dir=tmp_path))
    path = Path(result['outputs'][0]['path'])
    assert path.suffix == suffix
    assert path.read_bytes() == raw


def test_status_hands_safe_native_overrides_to_host(tmp_path):
    import json
    from papervizagent.ops import StatusInput, status
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({
        'roles': {'critic': {'provider': 'native', 'api_key': 'private-key',
                             'options': {'effort': 'high', 'api_token': 'private-token',
                                         'extra_headers': {'Authorization': 'private-header'}}}},
        'pipeline': {'work_dir': '/papers/custom', 'dataset_name': 'PaperBananaBench',
                     'split_name': 'demo', 'timestamp': 'run-1', 'auth_token': 'private-pipeline'},
    }))
    result = status(StatusInput(native=['llm', 'vlm'], model_policy='quality'),
                    Context(config={'papervizagent_config': str(config)}, data_dir=tmp_path))
    assert result['model_policy'] == 'quality'
    assert result['routes']['planner']['llm']['provider'] == 'native'
    assert result['routes']['visualizer']['image']['provider'] == 'codex'
    critic = result['routes']['critic']['vlm']
    assert critic['options'] == {'effort': 'high'}
    assert critic['unavailable_options'] == ['api_token', 'extra_headers']
    assert result['pipeline']['work_dir'] == '/papers/custom'
    assert result['pipeline']['split_name'] == 'demo'
    assert 'private-' not in json.dumps(result)


async def test_models_reports_missing_vision_without_hiding_catalog(tmp_path):
    from papervizagent.model_selection import ModelSelection
    from papervizagent.ops import EmptyInput, models
    with patch('papervizagent.ops.Backend') as cls:
        backend = cls.return_value.__aenter__.return_value
        backend.models = [{'id': 'text-only', 'model': 'text-only'}]
        backend.settings.model_policy = 'balanced'
        backend.codex = AsyncMock()
        backend.codex.return_value.request = AsyncMock()
        backend.codex.return_value.request.return_value = Mock()
        backend.codex.return_value.request.return_value.model_dump.return_value = {'imageGeneration': False}
        backend.select_model = Mock(side_effect=[ModelSelection('text-only', 'server_default_fallback'),
                                            ValueError('No vision model'),
                                            ModelSelection('text-only', 'server_default_fallback')])
        result = await models(EmptyInput(), Context(config={}, data_dir=tmp_path))
    assert result['models'] == backend.models
    assert result['defaults']['vlm'] == {'unavailable': 'No vision model'}
    assert result['defaults']['llm']['model'] == 'text-only'
    assert result['capabilities']['imageGeneration'] is False
