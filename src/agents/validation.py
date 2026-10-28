from __future__ import annotations

import json

from src.llm import complete_json
from src.schema import CandidateRequirement, GateResult
from src.utils import read_prompt


def validate(source_text: str, candidates: list[CandidateRequirement]) -> list[GateResult]:
    if not candidates:
        return []
    data = complete_json(
        system=read_prompt("validation_gate.txt"),
        user=json.dumps(
            {
                "source_text": source_text,
                "candidates": [c.model_dump() for c in candidates],
            }
        ),
    )
    by_id = {c.id: c for c in candidates}
    results: list[GateResult] = []
    for raw in data.get("results") or []:
        if not isinstance(raw, dict):
            continue
        result = GateResult.model_validate(raw)
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
