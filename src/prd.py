from __future__ import annotations

from src.schema import GateResult, Ticket


def _cell(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _bullets(lines: list[str], empty: str) -> str:
    if not lines:
        return empty
    return "\n".join(f"- {line}" for line in lines)


def render_prd(
    *,
    tickets: list[Ticket],
    rejected: list[GateResult],
    needs_clarification: list[GateResult],
    source_excerpt: str,
    priority_rule: str,
) -> str:
    users = sorted({ticket.user for ticket in tickets if ticket.user})
    problems = [f"{ticket.id}: {ticket.problem}" for ticket in tickets if ticket.problem]
    metrics = [f"{ticket.id}: {ticket.success_metric}" for ticket in tickets if ticket.success_metric]
    out_of_scope = [item for ticket in tickets for item in ticket.out_of_scope]
    rejected_lines = [
        f"{gate.requirement_id}: {'; '.join(gate.reasons) or 'rejected'}" for gate in rejected
    ]
    questions: list[str] = []
    for gate in needs_clarification:
        for question in gate.clarification_questions or ["Add the missing detail."]:
            questions.append(f"{gate.requirement_id}: {question}")

    rows = [
        "| Rank | Ticket | Title | Priority | Why this order |",
        "| --- | --- | --- | --- | --- |",
    ]
    for ticket in tickets:
        rows.append(
            "| "
            + " | ".join(
                [
                    _cell(ticket.rice.rank),
                    _cell(ticket.id),
                    _cell(ticket.title),
                    _cell(ticket.priority),
                    _cell(ticket.order_reason),
                ]
            )
            + " |"
        )
    if not tickets:
        rows.append("|  |  | No ticket passed the developer-agent check. |  |  |")

    scope = [
        f"{ticket.rice.rank}. {ticket.id} — {ticket.title} ({ticket.priority})" for ticket in tickets
    ]
    sections = [
        "# PRD",
        "",
        "## Problem",
        _bullets(problems, "Not stated in the source."),
        "",
        "## Users",
        _bullets(users, "Not stated in the source."),
        "",
        "## Success metrics",
        _bullets(metrics, "Not stated in the source."),
        "",
        "## In scope",
        _bullets(scope, "Nothing is in scope yet. No ticket passed the developer-agent check."),
        "",
        "## Not in this batch",
        "These asks need an answer before they can move to the next phase.",
        "",
        _bullets(questions, "None."),
        "",
        "## Rejected",
        "These asks are not turned into tickets from this request.",
        "",
        _bullets(rejected_lines, "None."),
        "",
        "## Explicitly out of scope",
        _bullets(out_of_scope, "Not stated in the source."),
        "",
        "## Prioritized requirements",
        "\n".join(rows),
        "",
        "## Order",
        priority_rule or "Rank 1 is first in this batch. Priority is high, medium, or low.",
        "",
        "## Definition of ready",
        "A ticket is in scope for the next phase only when a developer or a coding agent can implement it from the ticket and this PRD:",
        "- The user is a phrase from the source.",
        "- The context, such as a screen, API, or data set, is a phrase from the source.",
        "- The problem is stated.",
        "- At least one acceptance criterion is specific enough to test.",
        "- A source quote is attached.",
        "- No question is still open.",
        "",
        "## Source",
        source_excerpt or "No request text was provided.",
        "",
    ]
    return "\n".join(sections)
