from __future__ import annotations

from datetime import datetime

from src.schema import AgentStep
from src.utils import ROOT

_LABEL = {"rice": "ordering"}


class TraceLog:
    """Append one line each time an agent finishes, so the file matches the run."""

    def __init__(self) -> None:
        folder = ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        self.path = folder / f"trace-{stamp}.log"
        self.relative = str(self.path.relative_to(ROOT))
        self.steps: list[AgentStep] = []
        self.path.write_text("step\ttime\tagent\tcount\twhat happened\n", encoding="utf-8")

    def add(self, step: AgentStep) -> None:
        self.steps.append(step)
        name = _LABEL.get(step.agent, step.agent)
        clock = datetime.now().strftime("%H:%M:%S")
        line = f"{len(self.steps):02d}\t{clock}\t{name}\t{step.count}\t{step.summary}\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
