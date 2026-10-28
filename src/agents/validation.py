from __future__ import annotations

import json

from pydantic import ValidationError

from src.llm import complete_json
from src.schema import CandidateRequirement, GateResult
from src.utils import read_prompt

_DECISION_ALIASES = {
    "ready": "ready",
    "pass": "ready",
    "passed": "ready",
    "accept": "ready",
    "accepted": "ready",
    "approved": "ready",
    "rejected": "rejected",
    "reject": "rejected",
    "fail": "rejected",
    "failed": "rejected",
    "deny": "rejected",
    "denied": "rejected",
    "needs_clarification": "needs_clarification",
    "need_clarification": "needs_clarification",
    "clarification": "needs_clarification",
    "clarify": "needs_clarification",
    "needsclarification": "needs_clarification",
    "question": "needs_clarification",
    "questions": "needs_clarification",
}


def normalize_decision(value: object) -> str:
    """Map model wording onto ready, needs_clarification, or rejected."""
    if not isinstance(value, str):
        return "needs_clarification"
    key = value.strip().lower().replace("-", " ").replace("_", " ")
    key = "_".join(key.split())
    return _DECISION_ALIASES.get(key, "needs_clarification")


def validate(
    source_text: str,
    candidates: list[CandidateRequirement],
    project_context: str = "",
) -> list[GateResult]:
    if not candidates:
        return []
    data = complete_json(
        system=read_prompt("validation_gate.txt"),
        user=json.dumps(
            {
                "source_text": source_text,
                "project_context": project_context,
                "candidates": [c.model_dump() for c in candidates],
            }
        ),
    )
    by_id = {c.id: c for c in candidates}
    results: list[GateResult] = []
    for raw in data.get("results") or []:
        if not isinstance(raw, dict):
            continue
        raw["decision"] = normalize_decision(raw.get("decision"))
        if raw.get("requirement_id") is not None:
            raw["requirement_id"] = str(raw["requirement_id"])
        for key in ("reasons", "clarification_questions", "source_quotes", "context_quotes"):
            if raw.get(key) is None:
                raw[key] = []
        try:
            result = GateResult.model_validate(raw)
        except ValidationError:
            req_id = str(raw.get("requirement_id") or "unknown")
            results.append(
                GateResult(
                    requirement_id=req_id,
                    decision="needs_clarification",
                    reasons=["Gate returned a decision this app could not read."],
                    clarification_questions=["Please restate this requirement with actor, context, and a success check."],
                    source_quotes=by_id[req_id].source_quotes if req_id in by_id else [],
                )
            )
            continue
        if result.requirement_id in by_id and not result.source_quotes:
            result.source_quotes = by_id[result.requirement_id].source_quotes
        results.append(result)
    missing = {c.id for c in candidates} - {r.requirement_id for r in results}
    for req_id in missing:
        candidate = by_id[req_id]
        results.append(
            GateResult(
                requirement_id=req_id,
                decision="needs_clarification",
                reasons=["Gate did not return a decision for this candidate."],
                clarification_questions=["Please restate this requirement with actor, context, and a success check."],
                source_quotes=candidate.source_quotes,
            )
        )
    return results
