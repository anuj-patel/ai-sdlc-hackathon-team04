from __future__ import annotations

import json

from pydantic import ValidationError

from src.llm import complete_json
from src.schema import CandidateRequirement, GateResult, Ticket
from src.utils import read_prompt

_PRIORITY = {
    "high": "high",
    "medium": "medium",
    "low": "low",
    "highest": "high",
    "urgent": "high",
    "normal": "medium",
}
_TYPE = {
    "feature": "feature",
    "bug": "bug",
    "chore": "chore",
    "improvement": "improvement",
    "task": "chore",
    "story": "feature",
}


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _coerce(raw: dict, index: int) -> dict:
    raw.setdefault("id", f"T-{index}")
    raw["id"] = str(raw["id"])
    raw["status"] = "ready"
    priority = str(raw.get("priority") or "medium").strip().lower()
    raw["priority"] = _PRIORITY.get(priority, "medium")
    ticket_type = str(raw.get("type") or "feature").strip().lower()
    raw["type"] = _TYPE.get(ticket_type, "feature")
    for key in ("acceptance_criteria", "source_quotes", "dependencies", "out_of_scope"):
        raw[key] = _as_list(raw.get(key))
    for key in ("problem", "user", "context", "success_metric", "title", "description", "order_reason"):
        if raw.get(key) is None:
            raw[key] = ""
        else:
            raw[key] = str(raw[key])
    try:
        score = float(raw.get("confidence_score", 0.5))
    except (TypeError, ValueError):
        score = 0.5
    if score > 1 and score <= 100:
        score = score / 100
    raw["confidence_score"] = min(1.0, max(0.0, score))
    questions = raw.get("clarification_questions")
    raw["clarification_questions"] = _as_list(questions) or None
    return raw


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
        try:
            tickets.append(Ticket.model_validate(_coerce(raw, index)))
        except ValidationError:
            continue
    return tickets
