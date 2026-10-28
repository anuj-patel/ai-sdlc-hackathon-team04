from __future__ import annotations

from collections.abc import Callable

from src.agents.developer_check import apply_developer_check
from src.agents.extraction import extract
from src.agents.gatekeepers import block_vague_ready, filter_vague_tickets
from src.agents.rice import rank_tickets
from src.agents.ticket_writer import write_tickets
from src.agents.traceability import check_context_quotes, filter_tickets, split_candidates
from src.agents.validation import validate
from src.github_context import clip_context, fetch_readme, parse_repo
from src.prd import render_prd
from src.schema import AgentStep, GateResult, PipelineResult, Ticket
from src.trace_log import write_trace
from src.tracker import render_tracker_csv, render_tracker_markdown
from src.utils import excerpt


def orchestrate(
    text: str,
    project_context: str = "",
    repo: str | None = None,
    on_progress: Callable[[str, str], None] | None = None,
) -> PipelineResult:
    """Run extraction, traceability, validation, tickets, the developer check, and RICE."""

    def report(agent: str, message: str) -> None:
        if on_progress is not None:
            on_progress(agent, message)

    source = text or ""
    context = (project_context or "").strip()
    repo_value = (repo or "").strip()
    trace: list[AgentStep] = [
        AgentStep(
            agent="orchestrator",
            summary="Routing extraction, traceability, validation, the developer check, and ordering.",
            count=6,
        )
    ]

    report("orchestrator", "Choosing the order. This agent does not write tickets.")
    if repo_value:
        owner, name = parse_repo(repo_value)
        readme = fetch_readme(repo_value)
        block = f"GitHub README for {owner}/{name}\n\n{readme}"
        context = f"{context}\n\n{block}".strip() if context else block
        trace.append(
            AgentStep(
                agent="orchestrator",
                summary=f"Loaded the README from {owner}/{name} as the project document.",
                count=1,
            )
        )

    context_for_model = clip_context(context)
    if not source.strip():
        report("orchestrator", "Input is empty. Stopping before extraction.")
        trace.append(AgentStep(agent="orchestrator", summary="Input is empty. Stopped before extraction.", count=0))
        return _finish(
            trace,
            tickets=[],
            rejected=[],
            needs_clarification=[],
            gates=[],
            candidates=[],
            source=source,
            context=context_for_model,
            repo=repo_value,
        )

    report("extraction", "Reading the text and splitting it into separate asks, called candidates.")
    candidates = extract(source)
    trace.append(
        AgentStep(
            agent="extraction",
            summary=f"Extracted {len(candidates)} candidate requirement(s) with source quotes.",
            count=len(candidates),
        )
    )

    report("traceability", "Checking that every quote appears in the text you pasted.")
    kept, invented = split_candidates(source, candidates)
    trace.append(
        AgentStep(
            agent="traceability",
            summary=f"Rejected {len(invented)} candidate(s) whose quotes are not in the source.",
            count=len(invented),
        )
    )

    report("validation", "Deciding ready, needs clarification, or rejected for each candidate.")
    validated = validate(source, kept, context_for_model) if kept else []
    validated = check_context_quotes(validated, context_for_model)
    report("gatekeeper", "Blocking vague ready asks that have no measurable outcome.")
    validated, blocked = block_vague_ready(validated)
    trace.append(
        AgentStep(
            agent="gatekeeper",
            summary=f"Overturned {blocked} ready decision(s) that used vague language.",
            count=blocked,
        )
    )
    ready = [gate for gate in validated if gate.decision == "ready"]
    clarify = [gate for gate in validated if gate.decision == "needs_clarification"]
    rejected_by_gate = [gate for gate in validated if gate.decision == "rejected"]
    context_note = "against the project document" if context_for_model else "with no project document attached"
    trace.append(
        AgentStep(
            agent="validation",
            summary=(
                f"Judged {len(validated)} candidate(s) {context_note}: "
                f"{len(ready)} ready, {len(clarify)} need clarification, {len(rejected_by_gate)} rejected."
            ),
            count=len(validated),
        )
    )

    report("ticket_writer", "Writing tickets only for candidates marked ready.")
    drafted = write_tickets(source, kept, ready)
    report("traceability", "Checking the ticket quotes against the text again.")
    tickets = filter_tickets(source, drafted)
    tickets, vague_tickets = filter_vague_tickets(tickets)
    dropped = len(drafted) - len(tickets)
    trace.append(
        AgentStep(
            agent="ticket_writer",
            summary=f"Drafted {len(drafted)} ticket(s) from ready requirements.",
            count=len(drafted),
        )
    )
    trace.append(
        AgentStep(
            agent="traceability",
            summary=(
                f"Kept {len(tickets)} ticket(s) and dropped {dropped}, "
                f"including {vague_tickets} blocked by the vague-language gatekeeper."
            ),
            count=len(tickets),
        )
    )

    report("developer", "Checking whether a developer could build each ticket without guessing.")
    passed, held = apply_developer_check(tickets, source, kept)
    trace.append(
        AgentStep(
            agent="developer",
            summary=(
                f"{len(passed)} ticket(s) passed the developer-agent check. "
                f"{len(held)} held back because a developer would still have to guess."
            ),
            count=len(passed),
        )
    )

    report("ordering", "Ordering the ready tickets in this batch.")
    ranked, ordering_note = rank_tickets(passed, source)
    first = f" First is {ranked[0].id} ({ranked[0].priority})." if ranked else ""
    trace.append(
        AgentStep(
            agent="rice",
            summary=f"Ordered {len(ranked)} ticket(s).{first} {ordering_note}".strip(),
            count=len(ranked),
        )
    )

    return _finish(
        trace,
        tickets=ranked,
        rejected=invented + rejected_by_gate,
        needs_clarification=clarify + held,
        gates=invented + validated + held,
        candidates=candidates,
        source=source,
        context=context_for_model,
        repo=repo_value,
        ordering_note=ordering_note,
    )


def _finish(
    trace: list[AgentStep],
    *,
    tickets: list[Ticket],
    rejected: list[GateResult],
    needs_clarification: list[GateResult],
    gates: list[GateResult],
    candidates: list,
    source: str,
    context: str,
    repo: str,
    ordering_note: str = "",
) -> PipelineResult:
    rule = ""
    if tickets or ordering_note:
        rule = "Rank 1 is first in this batch. Priority is high, medium, or low. A ticket that others depend on is ordered before them."
        if ordering_note:
            rule = f"{rule} {ordering_note}"
    excerpt_text = excerpt(source)
    result = PipelineResult(
        tickets=tickets,
        rejected=rejected,
        needs_clarification=needs_clarification,
        gates=gates,
        candidates=candidates,
        agent_trace=trace,
        input_excerpt=excerpt_text,
        project_context_excerpt=excerpt(context),
        repo=repo,
        priority_rule=rule,
        prd=render_prd(
            tickets=tickets,
            rejected=rejected,
            needs_clarification=needs_clarification,
            source_excerpt=excerpt_text,
            priority_rule=rule,
        ),
        tracker_markdown=render_tracker_markdown(tickets),
        tracker_csv=render_tracker_csv(tickets),
    )
    return result.model_copy(update={"trace_log": write_trace(trace)})
