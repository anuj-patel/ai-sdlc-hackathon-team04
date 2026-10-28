from __future__ import annotations

from src.agents.extraction import extract
from src.agents.ticket_writer import write_tickets
from src.agents.validation import validate
from src.schema import PipelineResult
from src.utils import excerpt


def run(text: str) -> PipelineResult:
    source = text or ""
    candidates = extract(source)
    gates = validate(source, candidates)
    rejected = [g for g in gates if g.decision == "rejected"]
    needs_clarification = [g for g in gates if g.decision == "needs_clarification"]
    ready = [g for g in gates if g.decision == "ready"]
    tickets = write_tickets(source, candidates, ready)
    return PipelineResult(
        tickets=tickets,
        rejected=rejected,
        needs_clarification=needs_clarification,
        candidates=candidates,
        input_excerpt=excerpt(source),
    )
