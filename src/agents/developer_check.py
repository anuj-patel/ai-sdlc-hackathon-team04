from __future__ import annotations

from src.agents.gatekeepers import is_vague
from src.agents.traceability import quote_in_source
from src.schema import CandidateRequirement, DeveloperCheck, GateResult, Ticket


def _grounded(value: str, source: str, fallback: str | None) -> str:
    if value and quote_in_source(value, source):
        return value.strip()
    if fallback and quote_in_source(fallback, source):
        return fallback.strip()
    return ""


def match_candidate(ticket: Ticket, candidates: list[CandidateRequirement]) -> CandidateRequirement | None:
    quotes = set(ticket.source_quotes)
    best: CandidateRequirement | None = None
    best_count = 0
    for candidate in candidates:
        overlap = len(quotes & set(candidate.source_quotes))
        if overlap > best_count:
            best = candidate
            best_count = overlap
    return best


def fill_structure(ticket: Ticket, source: str, candidate: CandidateRequirement | None) -> Ticket:
    """Copy actor, context, and problem from text that is already in the source."""
    actor = candidate.actor if candidate else None
    context = candidate.context if candidate else None
    metric = candidate.success_metric if candidate else None
    problem = ticket.problem.strip()
    if not quote_in_source(problem, source):
        problem = ticket.source_quotes[0] if ticket.source_quotes else ""
    success = _grounded(ticket.success_metric, source, metric)
    if not success:
        for item in ticket.acceptance_criteria:
            if quote_in_source(item, source):
                success = item.strip()
                break
    return ticket.model_copy(
        update={
            "problem": problem,
            "user": _grounded(ticket.user, source, actor),
            "context": _grounded(ticket.context, source, context),
            "success_metric": success,
        }
    )


def review_ticket(ticket: Ticket, source: str) -> DeveloperCheck:
    """Would a developer or a coding agent still have to guess?"""
    gaps: list[str] = []
    questions: list[str] = []
    if not ticket.user.strip():
        gaps.append("User is missing or is not a phrase from the source.")
        questions.append("Who is the user or actor for this ticket? Use a phrase from the request.")
    if not ticket.context.strip():
        gaps.append("Context is missing or is not a phrase from the source.")
        questions.append("Where does this happen: which screen, API, or data? Use a phrase from the request.")
    if not ticket.problem.strip():
        gaps.append("Problem is empty.")
        questions.append("What problem should this ticket solve, in the words of the request?")
    if not ticket.source_quotes:
        gaps.append("No source quote is attached.")
        questions.append("Which sentence in the request is this ticket based on?")
    testable = [
        item
        for item in ticket.acceptance_criteria
        if len(item.split()) >= 4 and not is_vague(item)
    ]
    if not testable:
        gaps.append("No acceptance criterion is specific enough to test.")
        questions.append("What observable outcome proves this is done?")
    if ticket.clarification_questions:
        gaps.append("The ticket still has open questions.")
        questions.extend(ticket.clarification_questions)
    if is_vague(ticket.title) or is_vague(ticket.description):
        gaps.append("The title or description still uses vague language.")
        questions.append("Replace the vague wording with an outcome a developer can test.")
    return DeveloperCheck(passed=not gaps, gaps=gaps, questions=questions)


def apply_developer_check(
    tickets: list[Ticket],
    source: str,
    candidates: list[CandidateRequirement],
) -> tuple[list[Ticket], list[GateResult]]:
    ready: list[Ticket] = []
    held: list[GateResult] = []
    for ticket in tickets:
        filled = fill_structure(ticket, source, match_candidate(ticket, candidates))
        check = review_ticket(filled, source)
        filled = filled.model_copy(update={"developer_check": check})
        if check.passed:
            ready.append(filled)
            continue
        held.append(
            GateResult(
                requirement_id=ticket.id,
                decision="needs_clarification",
                reasons=["developer-agent check: a developer would still have to guess.", *check.gaps],
                clarification_questions=check.questions,
                source_quotes=list(ticket.source_quotes),
            )
        )
    return ready, held
