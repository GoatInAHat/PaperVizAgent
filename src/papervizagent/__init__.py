"""PaperVizAgent's upstream pipeline with portable model routing."""

from .pipeline import InferenceBackend, run_pipeline

__all__ = ['InferenceBackend', 'run_pipeline']
