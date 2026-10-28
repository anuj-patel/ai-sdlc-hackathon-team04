from __future__ import annotations

import json

import streamlit as st

from src.pipeline import run

st.set_page_config(page_title="Vague → Tickets", layout="wide")
st.title("Vague requirements → verifiable tickets")
st.caption("Planning-stage gate. Vague and invented asks are rejected, not rewritten.")

source = st.text_area("Paste a transcript, email, or one-liner", height=220)
if st.button("Process", type="primary") and source.strip():
    with st.spinner("Running extraction → gates → tickets"):
        result = run(source)
    st.subheader("Ready tickets")
    if not result.tickets:
        st.info("No ready tickets.")
    for ticket in result.tickets:
        with st.expander(ticket.title, expanded=True):
            st.write(ticket.description)
            st.write("Acceptance criteria")
            st.write(ticket.acceptance_criteria)
            st.write("Source quotes")
            st.write(ticket.source_quotes)
            st.metric("confidence", ticket.confidence_score)
    col_r, col_q = st.columns(2)
    with col_r:
        st.subheader("Rejected")
        st.json([g.model_dump() for g in result.rejected])
    with col_q:
        st.subheader("Needs clarification")
        st.json([g.model_dump() for g in result.needs_clarification])
    st.download_button(
        "Download JSON",
        data=json.dumps(result.model_dump(), indent=2),
        file_name="tickets.json",
        mime="application/json",
    )
