from __future__ import annotations

from src.schema import Ticket

SECTION_HEADING = "## Ready tickets now in scope"


def ready_tickets_block(tickets: list[Ticket]) -> str:
    """Quotable section a later validation pass can check."""
    lines = [
        SECTION_HEADING,
        "",
        "These tickets were accepted from a planning pass and are in scope.",
        "A later request that contradicts a sentence in this section is a contradiction.",
        "",
    ]
    for ticket in tickets:
        lines.append(f"### {ticket.id} {ticket.title}")
        lines.append(f"Priority: {ticket.priority}.")
        if ticket.user:
            lines.append(f"User: {ticket.user}.")
        if ticket.context:
            lines.append(f"Where: {ticket.context}.")
        if ticket.problem:
            lines.append(ticket.problem)
        if ticket.acceptance_criteria:
            lines.append("Done when:")
            lines.extend(f"- {item}" for item in ticket.acceptance_criteria)
        for quote in ticket.source_quotes:
            lines.append(f"Source quote: {quote}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def merge_ready_tickets(document: str, tickets: list[Ticket]) -> str:
    """Insert or replace the ready-ticket section. The rest of the document stays."""
    block = ready_tickets_block(tickets)
    text = document or ""
    if SECTION_HEADING in text:
        text = text.split(SECTION_HEADING, 1)[0]
    if not text.strip():
        return block
    return f"{text.rstrip()}\n\n{block}"
