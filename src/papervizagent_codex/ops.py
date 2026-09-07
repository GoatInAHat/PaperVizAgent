"""The same operations are projected to CLI, MCP, web and native host plugins."""
from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .backends import Backend
from .config import Modality, Role, load_settings
from .toolfactory import Context, Operation


class StatusInput(BaseModel):
    native: list[Modality] = Field(default_factory=list, description='Capabilities verified by the calling host; never inferred from the host name.')


class EmptyInput(BaseModel):
    pass


class InferInput(BaseModel):
    role: Role
    modality: Modality
    system: str = ''
    contents: list[dict[str, Any]] = Field(default_factory=list)
    contents_file: str | None = Field(default=None, description='Optional local JSON file containing content blocks, useful for image handoffs.')
    options: dict[str, Any] = Field(default_factory=dict)


class GenerateInput(BaseModel):
    data: dict[str, Any] = Field(description='Upstream input dictionary, including content and visual_intent; polish accepts its upstream image fields.')
    settings: dict[str, Any] = Field(default_factory=dict, description='Upstream pipeline settings; overrides the configuration file pipeline section. No credentials.')
    num_candidates: int = Field(default=1, ge=1)
    max_concurrent: int = Field(default=4, ge=1)


def settings_for(ctx: Context):
    return load_settings(ctx.config.get('papervizagent_codex_config'))


def status(args: StatusInput, ctx: Context) -> dict:
    settings = settings_for(ctx)
    return {
        'routes': {role: {modality: settings.resolve(role, modality, tuple(args.native)).model_dump(exclude_none=True)
                         for modality in ('llm', 'vlm', 'image')}
                   for role in ('retriever', 'planner', 'stylist', 'visualizer', 'critic', 'vanilla', 'polish')},
        'native': args.native,
        'codex': 'Use models to verify subscription availability; host capabilities are supplied by the caller.',
        'pipeline': settings.pipeline,
    }


async def models(args: EmptyInput, ctx: Context) -> dict:
    from openai_codex.generated.v2_all import ModelProviderCapabilitiesReadResponse
    async with Backend(settings_for(ctx)) as backend:
        client = await backend.codex()
        caps = await client.request('modelProvider/capabilities/read', {}, response_model=ModelProviderCapabilitiesReadResponse)
        return {'models': backend.models, 'capabilities': caps.model_dump(by_alias=True),
                'image_model': 'Managed by Codex; models.image.model selects the coordinating model.'}


def _run_dir(ctx: Context) -> Path:
    path = ctx.data_dir / 'runs' / str(uuid4())
    path.mkdir(parents=True, exist_ok=False)
    return path


async def infer(args: InferInput, ctx: Context) -> dict:
    contents = json.loads(Path(args.contents_file).expanduser().read_text()) if args.contents_file else args.contents
    if not contents:
        raise ValueError('Supply contents or contents_file.')
    configured = settings_for(ctx)
    spec = configured.resolve(args.role, args.modality)
    spec.options = {**spec.options, **args.options}
    configured.roles[args.role] = spec
    async with Backend(configured) as backend:
        result = await backend.generate(args.role, args.modality, args.system, contents)
        if args.modality == 'image':
            path = _run_dir(ctx)
            outputs = []
            for i, value in enumerate(result):
                filename = path / f'image-{i}.png'
                filename.write_bytes(base64.b64decode(value, validate=True))
                outputs.append({'type': 'image', 'path': str(filename)})
        else:
            outputs = [{'type': 'text', 'text': value} for value in result]
        return {'outputs': outputs, 'trace': backend.trace}


async def generate(args: GenerateInput, ctx: Context) -> dict:
    from .pipeline import run_pipeline
    configured = settings_for(ctx)
    options = {**configured.pipeline, **args.settings}
    root = _run_dir(ctx)
    work_dir = Path(options.pop('work_dir', root)).expanduser().resolve()
    semaphore = asyncio.Semaphore(args.max_concurrent)
    async with Backend(configured) as backend:
        async def candidate(index):
            async with semaphore:
                data = {**args.data, 'candidate_id': index}
                result = await run_pipeline(backend, data, work_dir=work_dir, **options)
                result_path = root / f'candidate-{index}.json'
                result_path.write_text(json.dumps(result, indent=2))
                image_key = result.get('eval_image_field')
                artifact = None
                if image_key and result.get(image_key):
                    image_path = root / f'candidate-{index}.jpg'
                    image_path.write_bytes(base64.b64decode(result[image_key], validate=True))
                    artifact = str(image_path)
                if not artifact and options.get('exp_mode') != 'dev_retriever':
                    raise RuntimeError(f'Pipeline produced no final image. Inspect {result_path}')
                return {'candidate_id': index, 'artifact': artifact, 'result': str(result_path)}
        results = await asyncio.gather(*(candidate(i) for i in range(args.num_candidates)))
        trace_path = root / 'trace.json'
        trace_path.write_text(json.dumps(backend.trace, indent=2))
        return {'candidates': results, 'trace': str(trace_path)}


OPERATIONS = [
    Operation(name='status', description='Resolve per-role model routing using optional configuration and verified host capabilities. Does not call a model.', input=StatusInput, handler=status, requires=('fs',), annotations={'readOnlyHint': True}),
    Operation(name='models', description='Read models and capabilities available through the configured Codex subscription. No inference.', input=EmptyInput, handler=models, requires=('net', 'shell', 'secret'), annotations={'readOnlyHint': True}),
    Operation(name='infer', description='Run one isolated PaperVizAgent role using its configured provider or Codex fallback. Returns text or an image file and request trace.', input=InferInput, handler=infer, requires=('net', 'fs', 'shell', 'secret')),
    Operation(name='generate', description='Run upstream PaperVizAgent end to end, with configurable roles, modes, retrieval, candidates and critic rounds. Plot mode executes generated Python in a bounded subprocess.', input=GenerateInput, handler=generate, requires=('net', 'fs', 'shell', 'secret')),
]
