from __future__ import annotations

import re

from src.schema import GateResult, Ticket

_VAGUE = re.compile(
    r"\b(?:better|faster|nicer|prettier|polish|make it good|improve(?: the)? ux|improve user experience)\b",
    re.IGNORECASE,
)


def is_vague(text: str) -> bool:
    """True when the text uses a vague word and states no number."""
    if not text or not _VAGUE.search(text):
        return False
    return re.search(r"\d", text) is None


def block_vague_ready(gates: list[GateResult]) -> tuple[list[GateResult], int]:
    """Overturn a ready decision when its quotes are only vague language."""
    updated: list[GateResult] = []
    blocked = 0
    for gate in gates:
        if gate.decision == "ready" and any(is_vague(quote) for quote in gate.source_quotes):
            blocked += 1
            updated.append(
                gate.model_copy(
                    update={
                        "decision": "rejected",
                        "reasons": [
                            *gate.reasons,
                            "gatekeeper: vague language with no measurable outcome",
                        ],
                    }
                )
            )
            continue
        updated.append(gate)
    return updated, blocked


def filter_vague_tickets(tickets: list[Ticket]) -> tuple[list[Ticket], int]:
    kept: list[Ticket] = []
    dropped = 0
    for ticket in tickets:
        if ticket.status != "ready" or not ticket.acceptance_criteria:
            dropped += 1
            continue
        if any(is_vague(quote) for quote in ticket.source_quotes):
            dropped += 1
            continue
        kept.append(ticket)
    return kept, dropped
