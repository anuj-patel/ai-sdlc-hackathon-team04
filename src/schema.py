from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["high", "medium", "low"]
TicketType = Literal["feature", "bug", "chore", "improvement"]
TicketStatus = Literal["ready", "needs_clarification", "rejected"]
GateDecision = Literal["ready", "needs_clarification", "rejected"]


class CandidateRequirement(BaseModel):
    id: str
    statement: str
    source_quotes: list[str] = Field(default_factory=list)
    actor: str | None = None
    context: str | None = None
    success_metric: str | None = None


class GateResult(BaseModel):
    requirement_id: str
    decision: GateDecision
    reasons: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    source_quotes: list[str] = Field(default_factory=list)


class Ticket(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: Priority
    type: TicketType
    source_quotes: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: TicketStatus
    clarification_questions: list[str] | None = None
    dependencies: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    tickets: list[Ticket] = Field(default_factory=list)
    rejected: list[GateResult] = Field(default_factory=list)
    needs_clarification: list[GateResult] = Field(default_factory=list)
    candidates: list[CandidateRequirement] = Field(default_factory=list)
    input_excerpt: str = ""
