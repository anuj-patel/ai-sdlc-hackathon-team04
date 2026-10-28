from __future__ import annotations

from src.schema import CandidateRequirement, GateResult, Ticket


def normalize(text: str) -> str:
    return " ".join(text.split())


def quote_in_source(quote: str, source: str) -> bool:
    snippet = quote.strip()
    if not snippet or not source:
        return False
    if snippet in source:
        return True
    return normalize(snippet) in normalize(source)


def split_candidates(
    source: str, candidates: list[CandidateRequirement]
) -> tuple[list[CandidateRequirement], list[GateResult]]:
    kept: list[CandidateRequirement] = []
    rejected: list[GateResult] = []
    for candidate in candidates:
        good = [quote for quote in candidate.source_quotes if quote_in_source(quote, source)]
        if good:
            kept.append(candidate.model_copy(update={"source_quotes": good}))
            continue
        rejected.append(
            GateResult(
                requirement_id=candidate.id,
                decision="rejected",
                reasons=["quote not found in source"],
                source_quotes=list(candidate.source_quotes),
            )
        )
    return kept, rejected


def check_context_quotes(results: list[GateResult], project_context: str) -> list[GateResult]:
    if not project_context.strip():
        return [result.model_copy(update={"context_quotes": []}) for result in results]
    checked: list[GateResult] = []
    for result in results:
        valid = [quote for quote in result.context_quotes if quote_in_source(quote, project_context)]
        dropped = len(valid) != len(result.context_quotes)
        reasons = list(result.reasons)
        if dropped:
            reasons.append("Dropped context quotes that are not in the project document.")
        checked.append(result.model_copy(update={"context_quotes": valid, "reasons": reasons}))
    return checked


def filter_tickets(source: str, tickets: list[Ticket]) -> list[Ticket]:
    kept: list[Ticket] = []
    for ticket in tickets:
        good = [quote for quote in ticket.source_quotes if quote_in_source(quote, source)]
        if not good or not ticket.acceptance_criteria:
            continue
        kept.append(ticket.model_copy(update={"source_quotes": good}))
    return kept
