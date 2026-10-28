from __future__ import annotations

import re

from src.agents.traceability import quote_in_source
from src.schema import Ticket

PRIORITY_RULE = (
    "RICE score = Reach × Impact × Confidence / Effort. "
    "Rank 1 is the first ticket to do in this batch. "
    "A ticket that others depend on is ordered before them, even when its score is lower. "
    "Priority is the RICE band, not the sentence order. "
    "Reach, impact, and effort count as measurements only when the source states a count, an outcome size, or a duration. "
    "Otherwise those factors are estimates used to order this batch, and confidence is lowered. "
    "Do not compare a score from this batch with a score from another request."
)

_REACH = re.compile(
    r"(\d[\d,]*)\s+(?:users|customers|people|players|events|requests|sessions)\b",
    re.IGNORECASE,
)
_EFFORT = re.compile(
    r"(?:in|takes|take|effort(?: of)?|estimate(?:d| of)?|spend|spent)\s+"
    r"(\d+(?:\.\d+)?)\s*-?\s*(hours|hour|days|day|weeks|week|sprints|sprint)\b",
    re.IGNORECASE,
)
_EFFORT_EXPLICIT = re.compile(
    r"(\d+(?:\.\d+)?)\s*-?\s*(person-weeks|person-week|sprints|sprint)\b",
    re.IGNORECASE,
)
_IMPACT_WORD = re.compile(r"\b(revenue|churn|compliance|legal|outage|blocker)\b", re.IGNORECASE)


def _weeks(amount: float, unit: str) -> float:
    name = unit.lower()
    if name.startswith("hour"):
        return amount / 40
    if name.startswith("day"):
        return amount / 5
    if name.startswith("sprint"):
        return amount * 2
    return amount


def _ticket_text(ticket: Ticket) -> str:
    return " ".join(
        [
            ticket.title,
            ticket.problem,
            ticket.description,
            ticket.success_metric,
            *ticket.source_quotes,
            *ticket.acceptance_criteria,
        ]
    )


def score_ticket(ticket: Ticket, source: str) -> Ticket:
    blob = _ticket_text(ticket)
    reach_match = _REACH.search(blob)
    if reach_match and quote_in_source(reach_match.group(0), source):
        reach = float(reach_match.group(1).replace(",", ""))
        reach_stated = True
        reach_basis = f"Stated in the source: {reach_match.group(0)}."
    else:
        reach = 1.0
        reach_stated = False
        reach_basis = (
            "The source names an actor but not how many people. Reach is 1 for ordering this batch, not a headcount."
            if ticket.user.strip()
            else "No headcount is in the source. Reach is 1 so this batch can still be ordered."
        )

    impact_match = _IMPACT_WORD.search(blob)
    metric_has_number = bool(re.search(r"\d", ticket.success_metric)) and quote_in_source(ticket.success_metric, source)
    if impact_match and quote_in_source(impact_match.group(0), source):
        impact = 2.0
        impact_stated = True
        impact_basis = (
            f"Source names a business outcome ({impact_match.group(0)}). Impact is 2 on the RICE scale (high)."
        )
    elif metric_has_number:
        impact = 2.0
        impact_stated = True
        impact_basis = "The success check in the source includes a number. Impact is 2 on the RICE scale (high)."
    elif ticket.success_metric.strip() or ticket.acceptance_criteria:
        impact = 1.0
        impact_stated = False
        impact_basis = "A success check exists, but the source does not size the outcome. Impact is 1 for ordering only."
    else:
        impact = 0.5
        impact_stated = False
        impact_basis = "No sized outcome. Impact is 0.5 for ordering only."

    effort_match = _EFFORT.search(blob) or _EFFORT_EXPLICIT.search(blob)
    if effort_match and quote_in_source(effort_match.group(0), source):
        effort = _weeks(float(effort_match.group(1)), effort_match.group(2))
        effort_stated = True
        effort_basis = f"Stated in the source: {effort_match.group(0)}, counted as {effort:.2f} person-weeks."
    else:
        effort = float(max(1, len(ticket.acceptance_criteria)))
        effort_stated = False
        effort_basis = (
            f"The source states no duration. Effort is {effort:.0f}, the number of acceptance criteria, for ordering only."
        )

    confidence = ticket.confidence_score
    notes = [f"Starts at the ticket confidence {confidence:.2f}."]
    if not reach_stated:
        confidence *= 0.8
        notes.append("Reach is not a measurement, so confidence is multiplied by 0.8.")
    if not effort_stated:
        confidence *= 0.8
        notes.append("Effort is not a measurement, so confidence is multiplied by 0.8.")
    if not impact_stated:
        confidence *= 0.9
        notes.append("Impact is not sized in the source, so confidence is multiplied by 0.9.")
    confidence = round(min(1.0, max(0.1, confidence)), 2)
    divisor = effort if effort > 0 else 1.0
    score = round((reach * impact * confidence) / divisor, 2)
    rice = ticket.rice.model_copy(
        update={
            "reach": reach,
            "reach_basis": reach_basis,
            "reach_stated": reach_stated,
            "impact": impact,
            "impact_basis": impact_basis,
            "impact_stated": impact_stated,
            "confidence": confidence,
            "confidence_basis": " ".join(notes),
            "effort": round(effort, 2),
            "effort_basis": effort_basis,
            "effort_stated": effort_stated,
            "score": score,
        }
    )
    return ticket.model_copy(update={"rice": rice})


def _band(ticket: Ticket, count: int, top: float) -> str:
    score = ticket.rice.score or 0
    confidence = ticket.rice.confidence
    if count == 1:
        if confidence >= 0.8 and ticket.rice.reach_stated:
            return "high"
        return "medium"
    if confidence < 0.4:
        if count >= 3 or (top > 0 and score < top * 0.5):
            return "low"
        return "medium"
    if top > 0 and score >= top * 0.85:
        return "high"
    if top > 0 and score < top * 0.5:
        return "low"
    return "medium"


def rank_tickets(tickets: list[Ticket], source: str) -> tuple[list[Ticket], str]:
    """Order this batch. Dependencies first, then higher RICE score."""
    remaining = {ticket.id: score_ticket(ticket, source) for ticket in tickets}
    ordered: list[Ticket] = []
    note = ""
    while remaining:
        available = [
            ticket.id
            for ticket in remaining.values()
            if not any(dep in remaining for dep in ticket.dependencies)
        ]
        if not available:
            note = "Some tickets depend on each other in a cycle. Those were left in priority order."
            available = list(remaining)
        available.sort(key=lambda ticket_id: (-(remaining[ticket_id].rice.score or 0), ticket_id))
        ordered.append(remaining.pop(available[0]))

    dependents: dict[str, list[str]] = {}
    for ticket in ordered:
        for dep in ticket.dependencies:
            dependents.setdefault(dep, []).append(ticket.id)

    top = max((ticket.rice.score or 0) for ticket in ordered) if ordered else 0
    ranked: list[Ticket] = []
    for index, ticket in enumerate(ordered, start=1):
        if ticket.id in dependents:
            reason = (
                f"Ordered before {', '.join(dependents[ticket.id])} "
                "because those tickets depend on this one."
            )
        elif ticket.dependencies:
            present = [dep for dep in ticket.dependencies if any(item.id == dep for item in ordered)]
            reason = (
                f"Ordered after {', '.join(present)} because this ticket depends on them."
                if present
                else "Ordered by priority within this batch."
            )
        else:
            reason = "Ordered by priority within this batch."
        rice = ticket.rice.model_copy(update={"rank": index})
        ranked.append(
            ticket.model_copy(
                update={
                    "rice": rice,
                    "priority": _band(ticket, len(ordered), top),
                    "order_reason": reason,
                }
            )
        )
    return ranked, note
