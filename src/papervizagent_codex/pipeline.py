"""Public adapter around the pinned PaperVizAgent orchestration."""

from pathlib import Path
from typing import Any

from .upstream.agents.critic_agent import CriticAgent
from .upstream.agents.planner_agent import PlannerAgent
from .upstream.agents.polish_agent import PolishAgent
from .upstream.agents.retriever_agent import RetrieverAgent
from .upstream.agents.stylist_agent import StylistAgent
from .upstream.agents.vanilla_agent import VanillaAgent
from .upstream.agents.visualizer_agent import VisualizerAgent
from .upstream.utils.config import ExpConfig
from .upstream.utils.inference import InferenceBackend
from .upstream.utils.paperviz_processor import PaperVizProcessor


async def run_pipeline(
    backend: InferenceBackend,
    data: dict[str, Any],
    *,
    work_dir: str | Path,
    dataset_name: str = "PaperBananaBench",
    task_name: str = "diagram",
    split_name: str = "demo",
    exp_mode: str = "demo_full",
    retrieval_setting: str = "none",
    temperature: float = 1.0,
    max_critic_rounds: int = 3,
    plot_timeout_seconds: float = 30,
    plot_dpi: int = 300,
    do_eval: bool = False,
    timestamp: str | None = None,
    **upstream_options: Any,
) -> dict[str, Any]:
    """Run one upstream-compatible candidate with host-supplied inference.

    ``dataset_name``, ``split_name``, ``do_eval``, and ``timestamp`` mirror the
    upstream experiment settings. Provider and model selection stays entirely
    in ``backend``. Unknown options fail rather than being silently ignored.
    """
    if upstream_options:
        names = ", ".join(sorted(upstream_options))
        raise TypeError(f"unsupported upstream option(s): {names}")
    if max_critic_rounds < 0:
        raise ValueError("max_critic_rounds must be non-negative")
    if plot_timeout_seconds <= 0:
        raise ValueError("plot_timeout_seconds must be positive")
    if plot_dpi <= 0:
        raise ValueError("plot_dpi must be positive")
    config = ExpConfig(
        dataset_name=dataset_name,
        task_name=task_name,
        split_name=split_name,
        temperature=temperature,
        exp_mode=exp_mode,
        retrieval_setting=retrieval_setting,
        max_critic_rounds=max_critic_rounds,
        plot_timeout_seconds=plot_timeout_seconds,
        plot_dpi=plot_dpi,
        timestamp=timestamp,
        work_dir=Path(work_dir),
        backend=backend,
    )
    processor = PaperVizProcessor(
        exp_config=config,
        vanilla_agent=VanillaAgent(exp_config=config),
        planner_agent=PlannerAgent(exp_config=config),
        visualizer_agent=VisualizerAgent(exp_config=config),
        stylist_agent=StylistAgent(exp_config=config),
        critic_agent=CriticAgent(exp_config=config),
        retriever_agent=RetrieverAgent(exp_config=config),
        polish_agent=PolishAgent(exp_config=config),
    )
    candidate = dict(data)
    candidate.setdefault("max_critic_rounds", max_critic_rounds)
    return await processor.process_single_query(candidate, do_eval=do_eval)
