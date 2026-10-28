from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _client() -> OpenAI:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and paste a key from https://aistudio.google.com/apikey"
        )
    return OpenAI(api_key=api_key, base_url=GEMINI_OPENAI_BASE)


def complete_json(system: str, user: str) -> dict:
    """Call Gemini and parse a JSON object. Strips markdown fences if present."""
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = _client().chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return parse_json_object(raw)


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM returned JSON that is not an object")
    return data
