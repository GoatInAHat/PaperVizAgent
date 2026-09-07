"""Provider-selected image formats survive the host handoff unchanged."""
import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
    result = status(StatusInput(native=['llm', 'vlm']),
                    Context(config={'papervizagent_config': str(config)}, data_dir=tmp_path))
    critic = result['routes']['critic']['vlm']
    assert critic['options'] == {'effort': 'high'}
    assert critic['unavailable_options'] == ['api_token', 'extra_headers']
    assert result['pipeline']['work_dir'] == '/papers/custom'
    assert result['pipeline']['split_name'] == 'demo'
    assert 'private-' not in json.dumps(result)
