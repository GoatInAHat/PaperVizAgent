# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Adapted for PaperVizAgent-codex: provider calls are supplied by the host.

"""The narrow host-inference seam used by all vendored roles."""

from typing import Any, Literal, Protocol


Modality = Literal["llm", "vlm", "image"]


class InferenceBackend(Protocol):
    async def generate(
        self,
        role: str,
        modality: Modality,
        system: str,
        contents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> list[str]: ...


def normalize_contents(contents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize upstream's two image shapes to one provider-neutral shape."""
    normalized: list[dict[str, Any]] = []
    for item in contents:
        if item.get("type") != "image":
            normalized.append(item)
            continue
        source = item.get("source")
        if not isinstance(source, dict):
            source = {
                "type": "base64",
                "media_type": item.get("media_type", "image/jpeg"),
                "data": item.get("image_base64", item.get("data", "")),
            }
        normalized.append({"type": "image", "source": source})
    return normalized


def text_modality(contents: list[dict[str, Any]]) -> Modality:
    """A text-producing request is vision-capable exactly when it carries an image."""
    return "vlm" if any(item.get("type") == "image" for item in contents) else "llm"


async def generate_text(
    backend: InferenceBackend,
    *,
    role: str,
    system: str,
    contents: list[dict[str, Any]],
    temperature: float,
    candidate_count: int = 1,
    max_output_tokens: int = 50_000,
) -> list[str]:
    normalized = normalize_contents(contents)
    return await backend.generate(
        role=role,
        modality=text_modality(normalized),
        system=system,
        contents=normalized,
        options={
            "temperature": temperature,
            "candidate_count": candidate_count,
            "max_output_tokens": max_output_tokens,
        },
    )


async def generate_image(
    backend: InferenceBackend,
    *,
    role: str,
    system: str,
    contents: list[dict[str, Any]],
    temperature: float,
    aspect_ratio: str,
    image_size: str = "1k",
) -> list[str]:
    return await backend.generate(
        role=role,
        modality="image",
        system=system,
        contents=normalize_contents(contents),
        options={
            "temperature": temperature,
            "candidate_count": 1,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        },
    )
