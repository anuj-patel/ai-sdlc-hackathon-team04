from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agents.developer_check import review_ticket
from src.agents.gatekeepers import block_vague_ready, is_vague
from src.agents.rice import rank_tickets
from src.project_doc import SECTION_HEADING, merge_ready_tickets
from src.tracker import ticket_document
from src.agents.traceability import quote_in_source
from src.agents.validation import normalize_decision
from src.pipeline import run
from src.schema import GateResult, PipelineResult, Ticket

ROOT = Path(__file__).resolve().parent


def score_result(fixture: dict, result: PipelineResult) -> dict:
    """AI eval: counts, quote traceability, and planted phrases that must not ship as ready."""
    expected = fixture["expected"]
    source = fixture["input"]
    ready_n = len(result.tickets)
    checks = {
        "min_ready": ready_n >= expected.get("min_ready", 0),
        "max_ready": ready_n <= expected.get("max_ready", 99),
        "min_rejected": len(result.rejected) >= expected.get("min_rejected", 0),
        "min_clarify": len(result.needs_clarification) >= expected.get("min_clarify", 0),
        "quotes_in_source": all(
            quote_in_source(quote, source) for ticket in result.tickets for quote in ticket.source_quotes
        ),
        "no_vague_ready": not any(is_vague(quote) for ticket in result.tickets for quote in ticket.source_quotes),
    }
    for phrase in fixture.get("must_not_be_ready", []):
        hit = any(phrase.lower() in " ".join(ticket.source_quotes).lower() for ticket in result.tickets)
        checks[f"not_ready:{phrase}"] = not hit
    return checks


def evaluate_fixture(path: Path) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    result = run(fixture["input"])
    checks = score_result(fixture, result)
    return {
        "fixture": path.name,
        "pass": all(checks.values()),
        "got": {
            "ready": len(result.tickets),
            "rejected": len(result.rejected),
            "clarify": len(result.needs_clarification),
        },
        "expected": fixture["expected"],
        "checks": checks,
    }


def gatekeeper_eval() -> list[dict]:
    """Code checks. These do not call the model."""
    empty = run("   ")
    vague = block_vague_ready(
        [
            GateResult(
                requirement_id="REQ-1",
                decision="ready",
                source_quotes=["Make the dashboard faster"],
            )
        ]
    )
    concrete = block_vague_ready(
        [
            GateResult(
                requirement_id="REQ-2",
                decision="ready",
                source_quotes=["export the last 30 days of events as CSV"],
            )
        ]
    )
    measured = block_vague_ready(
        [
            GateResult(
                requirement_id="REQ-3",
                decision="ready",
                source_quotes=["Make the dashboard faster than 200ms"],
            )
        ]
    )
    cases = [
        {"name": "empty_input_stops", "pass": empty.tickets == [] and empty.candidates == []},
        {"name": "vague_ready_blocked", "pass": vague[0][0].decision == "rejected" and vague[1] == 1},
        {"name": "concrete_stays_ready", "pass": concrete[0][0].decision == "ready" and concrete[1] == 0},
        {"name": "measured_speed_stays_ready", "pass": measured[0][0].decision == "ready"},
        {"name": "vague_detector", "pass": is_vague("please improve the UX") and not is_vague("add a CSV export")},
        {
            "name": "decision_aliases",
            "pass": normalize_decision("reject") == "rejected"
            and normalize_decision("needs clarification") == "needs_clarification"
            and normalize_decision("pass") == "ready",
        },
        {"name": "trace_is_a_file", "pass": _trace_is_a_file(empty)},
        {"name": "developer_check_passes_clear", "pass": review_ticket(_clear_ticket(), _CLEAR).passed},
        {
            "name": "developer_check_holds_missing_user",
            "pass": not review_ticket(_clear_ticket().model_copy(update={"user": ""}), _CLEAR).passed,
        },
        {"name": "rice_orders_stated_reach_first", "pass": _rice_orders_stated_reach_first()},
        {"name": "rice_dependency_before_dependent", "pass": _rice_dependency_before_dependent()},
        {"name": "data_window_is_not_effort", "pass": _data_window_is_not_effort()},
        {"name": "ticket_hides_score_formula", "pass": _ticket_hides_score_formula()},
        {"name": "project_doc_takes_ready_tickets", "pass": _project_doc_takes_ready_tickets()},
    ]
    return cases


_CLEAR = (
    "On the settings page, the signed-in user can switch the theme between light and dark. "
    "The choice persists after reload."
)


def _clear_ticket() -> Ticket:
    return Ticket(
        id="T-1",
        title="Switch theme and keep the choice",
        problem="On the settings page, the signed-in user can switch the theme between light and dark.",
        user="signed-in user",
        context="settings page",
        description="On the settings page, the signed-in user can switch the theme between light and dark.",
        acceptance_criteria=["The choice persists after reload."],
        success_metric="The choice persists after reload.",
        priority="medium",
        type="feature",
        source_quotes=["The choice persists after reload."],
        confidence_score=0.9,
        status="ready",
    )


def _trace_is_a_file(result: PipelineResult) -> bool:
    exported = result.export_dict()
    log = ROOT / result.trace_log
    return "agent_trace" not in exported and bool(result.prd) and log.is_file() and "orchestrator" in log.read_text()


def _sample(ticket_id: str, **updates: object) -> Ticket:
    payload = dict(
        id=ticket_id,
        title="Show the player count",
        problem="Show the player count on the event card.",
        user="event director",
        context="event card",
        description="Show the player count on the event card.",
        acceptance_criteria=["The event card shows the player count."],
        priority="medium",
        type="feature",
        source_quotes=["Show the player count on the event card."],
        confidence_score=0.9,
        status="ready",
    )
    payload.update(updates)
    return Ticket(**payload)


def _rice_orders_stated_reach_first() -> bool:
    source = (
        "1000 users can export the last 30 days of events as CSV. Build it in 2 days. "
        "Show the player count on the event card."
    )
    large = _sample(
        "T-2",
        title="Export events",
        description="1000 users can export the last 30 days of events as CSV. Build it in 2 days.",
        source_quotes=[
            "1000 users can export the last 30 days of events as CSV.",
            "Build it in 2 days.",
        ],
        success_metric="export the last 30 days of events as CSV",
        acceptance_criteria=["The CSV includes the last 30 days of events."],
    )
    small = _sample("T-1")
    ranked, _note = rank_tickets([small, large], source)
    return [ticket.id for ticket in ranked] == ["T-2", "T-1"] and ranked[0].priority == "high"


def _rice_dependency_before_dependent() -> bool:
    source = (
        "1000 users can export the last 30 days of events as CSV. Build it in 2 days. "
        "Show the player count on the event card. The export depends on the player count."
    )
    first = _sample("T-1")
    second = _sample(
        "T-2",
        title="Export events",
        description="1000 users can export the last 30 days of events as CSV. Build it in 2 days.",
        source_quotes=["1000 users can export the last 30 days of events as CSV.", "Build it in 2 days."],
        success_metric="export the last 30 days of events as CSV",
        dependencies=["T-1"],
    )
    ranked, _note = rank_tickets([second, first], source)
    return [ticket.id for ticket in ranked] == ["T-1", "T-2"] and "depend" in ranked[0].order_reason.lower()


def _ticket_hides_score_formula() -> bool:
    text = ticket_document(_clear_ticket())
    return "RICE" not in text and "Reach" not in text and "Priority:" in text


def _project_doc_takes_ready_tickets() -> bool:
    once = merge_ready_tickets("Existing product scope.", [_clear_ticket()])
    twice = merge_ready_tickets(once, [_clear_ticket()])
    return (
        "Existing product scope." in twice
        and "signed-in user" in twice
        and twice.count(SECTION_HEADING) == 1
    )


def _data_window_is_not_effort() -> bool:
    source = "Export the last 30 days of events as CSV."
    ticket = _sample(
        "T-1",
        title="Export events",
        description="Export the last 30 days of events as CSV.",
        source_quotes=["Export the last 30 days of events as CSV."],
        success_metric="Export the last 30 days of events as CSV.",
        acceptance_criteria=["The CSV covers the last 30 days of events."],
    )
    ranked, _note = rank_tickets([ticket], source)
    return ranked[0].rice.effort_stated is False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(ROOT / "fixtures"))
    parser.add_argument(
        "--gatekeepers",
        action="store_true",
        help="Run the code gatekeepers only. Does not call the model.",
    )
    args = parser.parse_args()
    if args.gatekeepers:
        reports = gatekeeper_eval()
        print(json.dumps(reports, indent=2))
        failed = [item for item in reports if not item["pass"]]
        if failed:
            raise SystemExit(f"{len(failed)} gatekeeper check(s) failed")
        return
    paths = sorted(Path(args.fixtures).glob("*.json"))
    if not paths:
        raise SystemExit(f"No fixtures in {args.fixtures}")
    reports = [evaluate_fixture(path) for path in paths]
    print(json.dumps(reports, indent=2))
    failed = [item for item in reports if not item["pass"]]
    if failed:
        raise SystemExit(f"{len(failed)} fixture(s) failed")


if __name__ == "__main__":
    main()
