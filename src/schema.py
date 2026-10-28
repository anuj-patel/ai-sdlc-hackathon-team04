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
    context_quotes: list[str] = Field(default_factory=list)


class RiceScore(BaseModel):
    """RICE = Reach × Impact × Confidence / Effort. Unstated factors are estimates for this batch only."""

    reach: float | None = None
    reach_basis: str = ""
    reach_stated: bool = False
    impact: float | None = None
    impact_basis: str = ""
    impact_stated: bool = False
    confidence: float = 0.0
    confidence_basis: str = ""
    effort: float | None = None
    effort_basis: str = ""
    effort_stated: bool = False
    score: float | None = None
    rank: int | None = None


class DeveloperCheck(BaseModel):
    passed: bool = False
    gaps: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class Ticket(BaseModel):
    id: str
    title: str
    problem: str = ""
    user: str = ""
    context: str = ""
    description: str
    acceptance_criteria: list[str]
    success_metric: str = ""
    out_of_scope: list[str] = Field(default_factory=list)
    priority: Priority
    type: TicketType
    source_quotes: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: TicketStatus
    clarification_questions: list[str] | None = None
    dependencies: list[str] = Field(default_factory=list)
    order_reason: str = ""
    rice: RiceScore = Field(default_factory=RiceScore)
    developer_check: DeveloperCheck = Field(default_factory=DeveloperCheck)


AgentName = Literal[
    "orchestrator",
    "extraction",
    "traceability",
    "validation",
    "gatekeeper",
    "ticket_writer",
    "developer",
    "rice",
]


class AgentStep(BaseModel):
    agent: AgentName
    summary: str
    count: int = 0


class PipelineResult(BaseModel):
    tickets: list[Ticket] = Field(default_factory=list)
    rejected: list[GateResult] = Field(default_factory=list)
    needs_clarification: list[GateResult] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    candidates: list[CandidateRequirement] = Field(default_factory=list)
    agent_trace: list[AgentStep] = Field(default_factory=list)
    input_excerpt: str = ""
    project_context_excerpt: str = ""
    repo: str = ""
    prd: str = ""
    tracker_markdown: str = ""
    tracker_csv: str = ""
    trace_log: str = ""
    priority_rule: str = ""

    def export_dict(self) -> dict:
        """JSON for handoff. The agent log and the ordering math stay out of this payload."""
        data = self.model_dump(exclude={"agent_trace"})
        for ticket in data.get("tickets", []):
            rice = ticket.pop("rice", None) or {}
            ticket["rank"] = rice.get("rank")
        return data
