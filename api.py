from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import run
from src.schema import PipelineResult

app = FastAPI(title="Vague → Tickets")


class ProcessRequest(BaseModel):
    text: str


@app.post("/process", response_model=PipelineResult)
def process(body: ProcessRequest) -> PipelineResult:
    return run(body.text)
