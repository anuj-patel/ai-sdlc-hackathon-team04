from __future__ import annotations

from collections.abc import Callable

from src.agents.orchestrator import orchestrate
from src.schema import PipelineResult


def run(
    text: str,
    project_context: str = "",
    repo: str | None = None,
    on_progress: Callable[[str, str], None] | None = None,
) -> PipelineResult:
    return orchestrate(text, project_context=project_context, repo=repo, on_progress=on_progress)
