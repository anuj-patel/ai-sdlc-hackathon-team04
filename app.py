from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st

from src.github_context import fetch_readme
from src.jira_publisher import create_issues, issue_text, jira_settings
from src.pipeline import run
from src.project_doc import merge_ready_tickets
from src.schema import GateResult, PipelineResult, Ticket

ROOT = Path(__file__).resolve().parent
PROJECT_DOC = ROOT / "docs" / "PROJECT.md"
EVENT_DOC = ROOT / "docs" / "sample_event_product.md"

STARTERS = {
    "Vague one-liner": ROOT / "inputs" / "vague.txt",
    "Mixed email": ROOT / "inputs" / "email.txt",
    "Contradiction": ROOT / "inputs" / "contradiction.txt",
    "Clear request": ROOT / "inputs" / "clear_request.txt",
}


def _load_starter(path: str) -> None:
    st.session_state.source = Path(path).read_text(encoding="utf-8").strip()
    st.session_state.result = None
    st.session_state.jira_created = []
    st.session_state.clarify_round = st.session_state.get("clarify_round", 0) + 1


def _clarification_block(parsed: PipelineResult, answers: dict[str, str]) -> str:
    lines = ["Clarification from the user, entered on this page:"]
    for gate in parsed.needs_clarification:
        lines.append(gate.requirement_id)
        questions = gate.clarification_questions or ["Add the missing detail."]
        for index, question in enumerate(questions):
            answer = answers.get(f"{gate.requirement_id}-{index}", "").strip()
            if not answer:
                continue
            lines.append(f"Question: {question}")
            lines.append(f"Answer: {answer}")
    return "\n".join(lines)


def _run_pipeline() -> None:
    with st.status("Orchestrator is starting", expanded=True) as status:
        def on_progress(agent: str, message: str) -> None:
            status.update(label=f"Running now: {agent}", state="running")
            status.write(f"**{agent}.** {message}")

        try:
            st.session_state.result = run(
                st.session_state.source,
                project_context=st.session_state.project_doc,
                on_progress=on_progress,
            ).model_dump()
            st.session_state.jira_created = []
            status.update(label="All agents finished", state="complete")
        except Exception as error:
            st.session_state.result = None
            status.update(label="Stopped", state="error")
            st.error(str(error))


def _quote(text: str) -> None:
    st.markdown(f"<div class='quote'>{html.escape(text)}</div>", unsafe_allow_html=True)


def _render_gate(gate: GateResult) -> None:
    with st.container(border=True):
        st.markdown(f"**{gate.requirement_id}** · {gate.decision}")
        for reason in gate.reasons:
            st.write(reason)
        for quote in gate.source_quotes:
            st.caption("Source")
            _quote(quote)
        for quote in gate.context_quotes:
            st.caption("Project document")
            _quote(quote)


_AGENT_LABEL = {"rice": "ordering"}


def _queue_ready_tickets(payload: list[dict]) -> None:
    st.session_state.queued_doc_update = payload


def _render_ticket(ticket: Ticket) -> None:
    rank = ticket.rice.rank or "-"
    with st.expander(f"#{rank} · {ticket.id} · {ticket.title}", expanded=rank == 1):
        meta = st.columns(2)
        meta[0].write(f"Priority: {ticket.priority}")
        meta[1].write(f"Type: {ticket.type}")
        if ticket.order_reason:
            st.caption(ticket.order_reason)
        fields = st.columns(3)
        fields[0].markdown(f"**User**\n\n{ticket.user or 'Not stated'}")
        fields[1].markdown(f"**Context**\n\n{ticket.context or 'Not stated'}")
        fields[2].markdown(f"**Success check**\n\n{ticket.success_metric or 'Not stated'}")
        st.markdown("**Problem**")
        st.write(ticket.problem or "Not stated in the source.")
        st.markdown("**What to build**")
        st.write(ticket.description)
        st.markdown("**Acceptance criteria**")
        for item in ticket.acceptance_criteria:
            st.write(f"- {item}")
        if ticket.out_of_scope:
            st.markdown("**Out of scope**")
            for item in ticket.out_of_scope:
                st.write(f"- {item}")
        if ticket.dependencies:
            st.caption("Depends on " + ", ".join(ticket.dependencies))
        for quote in ticket.source_quotes:
            _quote(quote)


st.set_page_config(page_title="Vague → Tickets", layout="wide")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; max-width: 980px; }
    .agent-step {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 10px;
        padding: 0.55rem 0.8rem;
        margin-bottom: 0.35rem;
    }
    .quote {
        border-left: 3px solid #7c6af7;
        padding: 0.2rem 0.7rem;
        margin: 0.25rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "source" not in st.session_state:
    st.session_state.source = ""
if "project_doc" not in st.session_state:
    st.session_state.project_doc = ""
if "load_error" not in st.session_state:
    st.session_state.load_error = ""
if "clarify_round" not in st.session_state:
    st.session_state.clarify_round = 0
if "run_id" not in st.session_state:
    st.session_state.run_id = 0
if "jira_created" not in st.session_state:
    st.session_state.jira_created = []
if st.session_state.get("queued_doc_update"):
    incoming = [Ticket.model_validate(item) for item in st.session_state.pop("queued_doc_update")]
    st.session_state.project_doc = merge_ready_tickets(st.session_state.get("project_doc", ""), incoming)
    st.session_state.doc_notice = "Ready tickets are in the project document. The next run validates against them."
if st.session_state.get("queued_clarification"):
    addition = st.session_state.pop("queued_clarification")
    st.session_state.source = f"{st.session_state.source.rstrip()}\n\n{addition}"
    st.session_state.run_clarified = True

with st.sidebar:
    st.header("Setup")
    st.markdown("**Open this page**")
    st.caption("From the project folder: `source venv/bin/activate`, then `streamlit run app.py`. Open the Local URL, usually http://localhost:8501.")
    st.divider()
    st.markdown("**GitHub, optional**")
    st.caption("This reads a README into the document below. It does not sign you in and it does not create GitHub issues.")
    with st.form("github_readme", clear_on_submit=False):
        typed_repo = st.text_input("Repository", placeholder="https://github.com/owner/repo")
        load_submitted = st.form_submit_button("Load README", use_container_width=True)
    if load_submitted:
        try:
            readme = fetch_readme(typed_repo)
            existing = st.session_state.project_doc.strip()
            block = f"GitHub README for {typed_repo.strip()}\n\n{readme}"
            st.session_state.project_doc = f"{existing}\n\n{block}".strip() if existing else readme
            st.session_state.load_error = ""
        except (RuntimeError, ValueError) as error:
            st.session_state.load_error = str(error)
    doc_spec, doc_event = st.columns(2)
    if doc_spec.button("This project", use_container_width=True):
        st.session_state.project_doc = PROJECT_DOC.read_text(encoding="utf-8")
        st.session_state.load_error = ""
    if doc_event.button("Event sample", use_container_width=True):
        st.session_state.project_doc = EVENT_DOC.read_text(encoding="utf-8")
        st.session_state.load_error = ""
    if st.button("Clear document", use_container_width=True):
        st.session_state.project_doc = ""
        st.session_state.load_error = ""
    if st.session_state.load_error:
        st.error(st.session_state.load_error)
    notice = st.session_state.pop("doc_notice", "")
    if notice:
        st.success(notice)
    st.text_area("Project document", key="project_doc", height=180)
    st.caption("Add ready tickets from the Tickets tab. Doing that again replaces only that section. A public repo needs no token. A private repo needs `GITHUB_TOKEN` in `.env`, or `gh auth login`.")

st.title("Vague requirements → verifiable tickets")
st.caption("Paste a request, run the agents, answer any questions here, then confirm before anything goes to Jira.")

st.text_area("Paste a transcript, email, or one-liner", key="source", height=180)
starter_cols = st.columns(len(STARTERS))
for column, (label, path) in zip(starter_cols, STARTERS.items()):
    with column:
        st.button(label, use_container_width=True, on_click=_load_starter, args=(str(path),))

process_clicked = st.button("Process", type="primary", disabled=not st.session_state.source.strip())
run_clarified = st.session_state.pop("run_clarified", False)
if process_clicked or run_clarified:
    st.session_state.run_id += 1
    if process_clicked:
        st.session_state.clarify_round += 1
    _run_pipeline()

result_data = st.session_state.get("result")
if not result_data:
    st.info("The result shows up here: which agent ran, which asks are only candidates, and which ones became tickets.")
    st.stop()

parsed = PipelineResult.model_validate(result_data)

st.subheader("What just ran")
for step in parsed.agent_trace:
    st.markdown(
        f"<div class='agent-step'><strong>{html.escape(_AGENT_LABEL.get(step.agent, step.agent))}</strong> — {html.escape(step.summary)}</div>",
        unsafe_allow_html=True,
    )
if parsed.trace_log:
    st.caption(f"The agent log is saved in `{parsed.trace_log}`. Steps are numbered in the order each agent finishes. The log is not included in the JSON download.")
st.caption(
    "A candidate is one ask pulled from your text. It becomes a ticket only after validation, "
    "the vague-language gate, and the developer-agent check."
)

metrics = st.columns(4)
metrics[0].metric("Candidates", len(parsed.candidates), help="Asks found in the text. Not tickets yet.")
metrics[1].metric("Ready", len(parsed.tickets), help="Passed the developer-agent check and ordered for this batch.")
metrics[2].metric("Rejected", len(parsed.rejected), help="Vague, invented, contradictory, or out of scope.")
metrics[3].metric("Needs an answer", len(parsed.needs_clarification), help="A developer would still have to guess, or the gate asked a question.")

if parsed.needs_clarification:
    st.subheader("Needs an answer")
    st.caption("Type the missing detail, then click Use these answers. The agents do not continue until you do.")
    with st.form(f"clarification-{st.session_state.clarify_round}"):
        pending: dict[str, str] = {}
        for gate in parsed.needs_clarification:
            st.markdown(f"**{gate.requirement_id}**")
            for reason in gate.reasons:
                st.write(reason)
            questions = gate.clarification_questions or ["Add the missing detail."]
            for index, question in enumerate(questions):
                field = f"{gate.requirement_id}-{index}"
                pending[field] = st.text_area(question, key=f"clarify-{st.session_state.clarify_round}-{field}")
        allowed = st.form_submit_button("Use these answers", type="primary")
    if allowed:
        if not any(value.strip() for value in pending.values()):
            st.warning("Type at least one answer first.")
        else:
            st.session_state.queued_clarification = _clarification_block(parsed, pending)
            st.rerun()

detail_tab, ticket_tab, prd_tab, tracker_tab = st.tabs(
    ["Candidates and decisions", "Tickets", "PRD", "Tracker"]
)
gate_by_id = {gate.requirement_id: gate for gate in parsed.gates}

with detail_tab:
    if not parsed.candidates:
        st.info("No candidates were extracted.")
    for candidate in parsed.candidates:
        gate = gate_by_id.get(candidate.id)
        decision = gate.decision if gate else "pending"
        st.markdown(f"**{candidate.id}** · {decision}")
        st.write(candidate.statement)
        for quote in candidate.source_quotes:
            _quote(quote)
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("**Rejected**")
        if not parsed.rejected:
            st.caption("None.")
        for gate in parsed.rejected:
            _render_gate(gate)
    with right:
        st.markdown("**Needs an answer**")
        if not parsed.needs_clarification:
            st.caption("None.")
        for gate in parsed.needs_clarification:
            _render_gate(gate)

with ticket_tab:
    if not parsed.tickets:
        st.info("No ticket passed the developer-agent check. Answer the open questions, then run again.")
    else:
        st.caption("Rank 1 is first in this batch. Add these tickets to the project document when you want the next run to treat them as in scope.")
        st.table(
            [
                {
                    "Rank": ticket.rice.rank,
                    "Ticket": ticket.id,
                    "Title": ticket.title,
                    "Priority": ticket.priority,
                }
                for ticket in parsed.tickets
            ]
        )
        for ticket in parsed.tickets:
            _render_ticket(ticket)
        st.button(
            "Add ready tickets to the project document",
            type="primary",
            on_click=_queue_ready_tickets,
            args=([ticket.model_dump() for ticket in parsed.tickets],),
        )

with prd_tab:
    st.caption("This is the handoff document for the next phase. Empty sections were not in the source.")
    st.markdown(parsed.prd or "No PRD yet.")

with tracker_tab:
    st.caption("These rows are ready to import into a tracker. Only tickets that passed the developer-agent check are included.")
    if not parsed.tickets:
        st.info("Nothing to import yet.")
    else:
        st.code(parsed.tracker_csv, language="csv")

download_cols = st.columns(4)
download_cols[0].download_button(
    "Download JSON",
    data=json.dumps(parsed.export_dict(), indent=2),
    file_name="tickets.json",
    mime="application/json",
)
download_cols[1].download_button(
    "Download PRD",
    data=parsed.prd,
    file_name="prd.md",
    mime="text/markdown",
)
download_cols[2].download_button(
    "Download tracker CSV",
    data=parsed.tracker_csv,
    file_name="tracker.csv",
    mime="text/csv",
)
log_path = ROOT / parsed.trace_log if parsed.trace_log else None
if log_path and log_path.is_file():
    download_cols[3].download_button(
        "Download agent log",
        data=log_path.read_text(encoding="utf-8"),
        file_name=log_path.name,
        mime="text/plain",
    )

st.divider()
st.subheader("Jira")
st.caption("Nothing is created until you tick the tickets and confirm. Only tickets that passed the developer-agent check are listed.")
if not parsed.tickets:
    st.info("Tracker-ready tickets show up here. Rejected asks, and tickets a developer would still have to guess, are not sent.")
else:
    if jira_settings() is None:
        st.warning("Add JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY to .env before creating issues.")
    chosen: list[Ticket] = []
    for ticket in parsed.tickets:
        if st.checkbox(
            f"{ticket.id} · {ticket.title}",
            key=f"jira-{st.session_state.run_id}-{ticket.id}",
        ):
            chosen.append(ticket)
    if chosen:
        with st.expander("Preview of what Jira will receive", expanded=True):
            for ticket in chosen:
                st.markdown(f"**{ticket.title}**")
                st.text(issue_text(ticket))
    confirm = st.checkbox(
        "I confirm these tickets should be created in Jira",
        key=f"jira-ok-{st.session_state.run_id}",
    )
    if st.button("Create Jira issues", type="primary", disabled=not chosen or not confirm):
        try:
            st.session_state.jira_created = create_issues(chosen)
        except Exception as error:
            st.error(str(error))
    for created in st.session_state.jira_created:
        st.success(f"Created {created['key']}")
        st.markdown(f"[{created['url']}]({created['url']})")
