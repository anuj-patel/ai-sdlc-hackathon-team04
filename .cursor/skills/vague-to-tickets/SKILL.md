---
name: vague-to-tickets
description: >-
  Turns a transcript, email, or one-liner into gated tickets by orchestrating
  extraction, traceability, validation, and ticket writing. Use when the user
  asks to turn vague requirements into tickets, check a request against a
  project document, or load a GitHub repository README for validation.
---

# Vague requirements → verifiable tickets

You are the orchestrator. You do not extract requirements, judge them, or write tickets yourself.

## Inputs

- Requirement text: a transcript, email, or one-liner.
- Optional project document: `docs/PROJECT.md` is the spec for this system. Another file, or a GitHub README, may replace it.
- Optional GitHub repo: `https://github.com/owner/repo` or `owner/repo`.

## Run the pipeline

From the repo root, with the virtualenv active and `GEMINI_API_KEY` set:

```bash
python main.py --text "..." --context docs/PROJECT.md
python main.py --input inputs/email.txt --context docs/sample_event_product.md
python main.py --text "..." --repo https://github.com/owner/repo
```

`--repo` reads that repository's README and the validation subagent checks the request against it. Pass `--context` as well when both a local document and a README should apply.

The command prints JSON without the agent steps. Read the path in `trace_log` (`logs/trace-*.log`) for the steps, in this order:

1. orchestrator
2. extraction
3. traceability
4. validation
5. gatekeeper
6. ticket_writer
7. traceability
8. developer
9. rice

Then show the PRD, the tracker CSV, ready tickets, rejected gates, and needs-clarification gates. Quote `source_quotes` from the request and `context_quotes` from the project document. Do not add requirements that are not in the command output.

## Subagents

If `GEMINI_API_KEY` is missing, do not invent tickets. Run the same stages yourself by launching one `generalPurpose` subagent per stage, in order. Each subagent sees only its brief and the previous stage's JSON.

1. Read [extraction.md](extraction.md). Pass only the requirement text.
2. Apply [traceability.md](traceability.md) to the candidates. This stage is code, not a judgment.
3. Read [validation.md](validation.md). Pass the requirement text, the project document or README, and the surviving candidates.
4. Read [ticket-writer.md](ticket-writer.md). Pass only candidates the gate marked ready.
5. Apply [traceability.md](traceability.md) again to the tickets.
6. Read [developer-check.md](developer-check.md). Hold back any ticket a developer would still have to guess.
7. Read [rice.md](rice.md). Rank only the tickets that passed the developer check.

Do not run these stages in parallel. Do not skip validation. Do not copy detail from the project document into a ticket to make a vague line look ready.

## UI

```bash
streamlit run app.py
```

The project document starts empty. **This project** loads `docs/PROJECT.md`. **Load README** appends that repository's README. **Clear** removes the document. **Event sample** loads a different product. After a run, the page shows the PRD and a tracker CSV with rank and priority. **Add ready tickets to the project document** writes those tickets into the sidebar document and replaces that section if you add them again. The agent log is a file under `logs/`. Jira is created only after you confirm, and only for tickets that passed the developer check.
