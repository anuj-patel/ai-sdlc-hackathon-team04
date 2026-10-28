from __future__ import annotations

import json

from src.llm import complete_json
from src.schema import CandidateRequirement, GateResult, Ticket
from src.utils import read_prompt


def write_tickets(
    source_text: str,
    candidates: list[CandidateRequirement],
    ready: list[GateResult],
) -> list[Ticket]:
    if not ready:
        return []
    ready_ids = {g.requirement_id for g in ready}
    payload = [c.model_dump() for c in candidates if c.id in ready_ids]
    data = complete_json(
        system=read_prompt("ticket_writer.txt"),
        user=json.dumps({"source_text": source_text, "ready_requirements": payload}),
    )
    tickets: list[Ticket] = []
    for index, raw in enumerate(data.get("tickets") or [], start=1):
        if not isinstance(raw, dict):
            continue
        raw.setdefault("id", f"T-{index}")
        raw.setdefault("status", "ready")
        tickets.append(Ticket.model_validate(raw))
    return tickets
