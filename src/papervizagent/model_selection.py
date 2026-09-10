"""Catalog-driven Codex coordinator selection without hard-coded model IDs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .config import ModelPolicy


@dataclass(frozen=True)
class ModelSelection:
    model: str
    reason: str
    classification: str | None = None


_LEGACY_MARKERS = ('previous-generation', 'deprecated', 'retired')
_POLICY_MARKERS = {
    'balanced': ('balanced', 'mid-tier'),
    'quality': ('most capable', 'flagship', 'frontier'),
}


def _text(entry: dict) -> str:
    return ' '.join(str(entry.get(key) or '') for key in ('description', 'displayName')).lower()


def _is_legacy(entry: dict) -> bool:
    text = _text(entry)
    return bool(entry.get('upgrade') or entry.get('upgradeInfo')) or any(marker in text for marker in _LEGACY_MARKERS)


def _eligible(entries: list[dict], modality: str) -> list[dict]:
    return [
        entry for entry in entries
        if not entry.get('hidden')
        and not entry.get('modelSpecialty')
        and (modality != 'vlm' or 'image' in (entry.get('inputModalities') or ()))
    ]


def _current(entries: list[dict]) -> list[dict]:
    current = [entry for entry in entries if not _is_legacy(entry)]
    return current or entries


def select_model(entries: list[dict], *, modality: str, policy: ModelPolicy,
                 explicit: str | None = None) -> ModelSelection:
    """Select a visible general coordinator from the account's current catalog.

    Catalog descriptions are advisory labels, not cost or benchmark metadata.
    They are used only when a provider explicitly labels a model balanced or
    quality-oriented; otherwise the provider's default remains authoritative.
    """
    eligible = _eligible(entries, modality)
    if explicit:
        selected = next((entry for entry in eligible if explicit in (entry.get('id'), entry.get('model'))), None)
        if selected is None:
            raise ValueError(f'Codex model {explicit!r} is unavailable for {modality}. Use models to inspect the account catalog. For image, model selects the Codex coordinator; its built-in image model is service-managed.')
        return ModelSelection(selected['model'], 'explicit', 'explicit')
    if not eligible:
        raise ValueError(f'No available visible general Codex model supports {modality}.')

    current = _current(eligible)
    markers = _POLICY_MARKERS[policy]
    classified = [entry for entry in current if any(marker in _text(entry) for marker in markers)]
    if classified:
        # The provider's catalog order is the final tie-breaker. Prefer a
        # current entry without migration metadata when labels otherwise tie.
        selected = next((entry for entry in classified if not _is_legacy(entry)), classified[0])
        return ModelSelection(selected['model'], f'{policy}_catalog_label', policy)
    default = next((entry for entry in current if entry.get('isDefault')), None)
    if default:
        return ModelSelection(default['model'], 'server_default_fallback', None)
    return ModelSelection(current[0]['model'], 'catalog_order_fallback', None)


def automatic_effort(entry: dict, *, policy: ModelPolicy, modality: str) -> tuple[str | None, str | None]:
    """Choose a supported non-delegating effort for policy-selected calls."""
    supported = {
        value.get('reasoningEffort')
        for value in entry.get('supportedReasoningEfforts') or ()
        if value.get('reasoningEffort')
    }
    preferences = ('high', 'medium', 'low') if policy == 'quality' else (
        ('low', 'medium') if modality == 'image' else ('medium', 'low')
    )
    effort = next((value for value in preferences if value in supported), None)
    return effort, 'policy_effort' if effort else None


def selected_entry(entries: list[dict], model: str) -> dict:
    return next(entry for entry in entries if model in (entry.get('id'), entry.get('model')))


def validate_controls(entry: dict, options: dict) -> None:
    if 'effort' in options:
        supported = {value.get('reasoningEffort') for value in entry.get('supportedReasoningEfforts') or ()}
        if options['effort'] not in supported:
            raise ValueError(f"Codex model {entry['model']!r} does not support effort {options['effort']!r}.")
    if 'service_tier' in options:
        supported = {value.get('id') for value in entry.get('serviceTiers') or ()}
        if options['service_tier'] not in supported:
            raise ValueError(f"Codex model {entry['model']!r} does not support service_tier {options['service_tier']!r}.")
