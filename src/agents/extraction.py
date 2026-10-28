from __future__ import annotations

import json

from src.llm import complete_json
from src.schema import CandidateRequirement
from src.utils import read_prompt


def extract(source_text: str) -> list[CandidateRequirement]:
    data = complete_json(
        system=read_prompt("extraction.txt"),
        user=json.dumps({"source_text": source_text}),
    )
    candidates: list[CandidateRequirement] = []
    for index, raw in enumerate(data.get("candidates") or [], start=1):
        if not isinstance(raw, dict):
            continue
        raw.setdefault("id", f"REQ-{index}")
        candidates.append(CandidateRequirement.model_validate(raw))
    return candidates
