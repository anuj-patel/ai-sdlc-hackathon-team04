from __future__ import annotations

import csv
import io

from src.schema import Ticket


def _lines(items: list[str], empty: str) -> list[str]:
    if not items:
        return [empty]
    return [f"- {item}" for item in items]


def ticket_document(ticket: Ticket) -> str:
    """One tracker issue. A person can paste this without rewriting it."""
    sections = [
        f"{ticket.id} · {ticket.title}",
        "",
        f"Type: {ticket.type}",
        f"Priority: {ticket.priority}",
        f"Rank: {ticket.rice.rank or '-'}",
        f"Order: {ticket.order_reason or 'Not ranked.'}",
        "",
        "Problem",
        ticket.problem or "Not stated in the source.",
        "",
        "User",
        ticket.user or "Not stated in the source.",
        "",
        "Context",
        ticket.context or "Not stated in the source.",
        "",
        "Description",
        ticket.description or "Not stated in the source.",
        "",
        "Success check",
        ticket.success_metric or "Not stated in the source.",
        "",
        "Acceptance criteria",
        *_lines(ticket.acceptance_criteria, "Not stated in the source."),
        "",
        "Out of scope",
        *_lines(ticket.out_of_scope, "Not stated in the source."),
        "",
        "Depends on",
        *_lines(ticket.dependencies, "None stated."),
        "",
        "Source quotes",
        *_lines(ticket.source_quotes, "None."),
    ]
    return "\n".join(sections)


def render_tracker_markdown(tickets: list[Ticket]) -> str:
    if not tickets:
        return "# Tracker\n\nNo ticket passed the developer-agent check, so there is nothing to import.\n"
    parts = ["# Tracker-ready issues", "", "Import only these issues. Each one passed the developer-agent check.", ""]
    for ticket in tickets:
        parts.append(ticket_document(ticket))
        parts.append("\n---\n")
    return "\n".join(parts)


def render_tracker_csv(tickets: list[Ticket]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Issue Type",
            "Summary",
            "Description",
            "Priority",
            "Rank",
            "Acceptance Criteria",
            "Labels",
        ]
    )
    for ticket in tickets:
        writer.writerow(
            [
                ticket.type,
                ticket.title,
                ticket_document(ticket),
                ticket.priority,
                ticket.rice.rank or "",
                " | ".join(ticket.acceptance_criteria),
                "developer-ready",
            ]
        )
    return buffer.getvalue()
