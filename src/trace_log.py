from __future__ import annotations

from datetime import datetime

from src.schema import AgentStep
from src.utils import ROOT


def write_trace(steps: list[AgentStep]) -> str:
    """Write one plain-text log for this run. Returns a path relative to the repo."""
    folder = ROOT / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = folder / f"trace-{stamp}.log"
    lines = [f"{step.agent}\t{step.count}\t{step.summary}" for step in steps]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))
