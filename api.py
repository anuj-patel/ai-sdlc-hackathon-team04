from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.pipeline import run
from src.schema import PipelineResult

app = FastAPI(title="Vague → Tickets")


class ProcessRequest(BaseModel):
    text: str
    project_context: str = ""
    repo: str | None = None


@app.post("/process", response_model=PipelineResult, response_model_exclude={"agent_trace"})
def process(body: ProcessRequest) -> PipelineResult:
    try:
        return run(body.text, project_context=body.project_context, repo=body.repo)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
