# Vague Requirement → Verifiable Tickets

**AI-SDLC Planning Stage Challenge**

Turn messy real-world inputs (meeting transcripts, emails, one-liners) into clean, actionable, gated tickets that any developer or AI coding agent can implement without guessing or inventing requirements.

---

## Problem Statement

**Goal:** Convert vague or incomplete requirements into verifiable, self-contained tickets.

**Key Constraints:**
- Inputs can be transcripts, emails, or short one-liners
- System must **reject** vague statements and invented requirements
- Output must be tickets that anyone (human or agent) can act on
- Stage: **Planning**
- Fixtures: 3–4 inputs with planted defects + answer key
- Bonus: Tracker-ready output **or** Developer-Agent check

---

## Solution Overview

We build a **multi-agent pipeline** (not a chatbot) that:

1. Ingests messy text
2. Extracts candidate requirements with source quotes
3. Runs hard **Validation Gates**
4. Generates structured, actionable tickets
5. Optionally pushes to a tracker or runs a developer-agent verification

The system is fully automated after the initial trigger.

---

## Architecture

```
User Input (transcript / email / one-liner)
        ↓
┌─────────────────────────────────────┐
│         Orchestrator Agent          │
└─────────────────────────────────────┘
        ↓
┌──────────────┬──────────────┬──────────────┐
│  Extraction  │  Validation  │ Ticket Writer│
│  Sub-Agent   │  Gate Agent  │  Sub-Agent   │
└──────────────┴──────────────┴──────────────┘
        ↓
┌─────────────────────────────────────┐
│     Traceability + Confidence       │
└─────────────────────────────────────┘
        ↓
Final Tickets (JSON)
        ↓
Optional: Developer-Agent Check  or  Tracker Publisher
```

### Agents & Responsibilities

| Agent                    | Role                                                                 |
|--------------------------|----------------------------------------------------------------------|
| **Orchestrator**         | Controls flow, handles state, retries, and final assembly            |
| **Extraction Sub-Agent** | Pulls atomic requirements + exact source quotes                      |
| **Validation Gate**      | Rejects vague, invented, incomplete, or contradictory requirements   |
| **Ticket Writer**        | Turns validated requirements into clean, implementable tickets       |
| **Traceability Agent**   | Ensures every ticket field is backed by source text                  |
| **Developer-Agent Check**| (Bonus) Simulates a coding agent trying to implement the ticket      |
| **Tracker Publisher**    | (Bonus) Creates real issues in Linear / GitHub / Jira                |

---

## Ticket Schema

Every ticket must follow this structure:

```python
class Ticket:
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]          # concrete, testable
    priority: "high" | "medium" | "low"
    type: "feature" | "bug" | "chore" | "improvement"
    source_quotes: List[str]                # exact text from input
    confidence_score: float                 # 0.0 – 1.0
    status: "ready" | "needs_clarification" | "rejected"
    clarification_questions: Optional[List[str]]
    dependencies: List[str]
```

---

## Validation Gates (Critical)

The system **must** reject or flag:

- Vague language (“make it better”, “improve UX”, “faster”)
- Invented requirements not present in the source
- Missing acceptance criteria
- Missing actor / context / success metric
- Internal contradictions

**Gate Outcomes:**
- `ready` → proceed to ticket generation
- `needs_clarification` → return specific questions
- `rejected` → return reason + source quote

---

## How the System is Invoked

| Method          | Description                                      | Priority |
|-----------------|--------------------------------------------------|----------|
| CLI             | `python main.py --input file.txt`                | Must     |
| API             | `POST /process` with JSON body                   | Must     |
| Streamlit UI    | Paste text → click Process                       | Must     |
| Tracker push    | Auto-create issues in Linear/GitHub              | Bonus    |
| Slack/Discord   | Bot command                                      | Nice     |

Once triggered, the entire pipeline runs **automatically**.

---

## Development Plan

### Phase 0 – Foundation (First 2–3 hours)
- [x] Project structure
- [ ] Pydantic Ticket schema
- [ ] Basic Extraction + Gate prompt
- [ ] Minimal working CLI

### Phase 1 – Core Pipeline
- [ ] Robust Extraction Sub-Agent
- [ ] Hard Validation Gates
- [ ] Ticket Writer with acceptance criteria
- [ ] Source quote traceability
- [ ] Confidence scoring

### Phase 2 – Quality & Evaluation
- [ ] Handle official fixtures (planted defects)
- [ ] Evaluation harness vs answer key
- [ ] Edge case handling (empty, pure noise, contradictions)

### Phase 3 – Bonus Features
- [ ] Developer-Agent Check (simulate implementation)
- [ ] Linear / GitHub Issues integration
- [ ] Full agent trace visibility in UI

### Phase 4 – Demo & Polish
- [ ] Streamlit interface with step-by-step visibility
- [ ] Clean README + demo script
- [ ] Submission packaging

---

## Recommended Tech Stack

| Layer              | Choice                          | Reason                              |
|--------------------|---------------------------------|-------------------------------------|
| Language           | Python 3.11+                    | Fast iteration                      |
| LLM                | Claude 4 Sonnet / GPT-4o        | Strong structured output + refusal  |
| Orchestration      | LangGraph                       | Clear state + gates                 |
| Schema             | Pydantic + Instructor           | Guaranteed valid tickets            |
| UI                 | Streamlit                       | Fastest professional demo           |
| Tracker (bonus)    | Linear API or GitHub Issues     | Clean integration                   |

**Lightweight alternative:** Sequential functions + strong prompts (no heavy framework) if time is very limited.

---

## Project Structure

```
vague-to-tickets/
├── src/
│   ├── schema.py              # Pydantic models
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── extraction.py
│   │   ├── validation.py
│   │   ├── ticket_writer.py
│   │   └── developer_check.py
│   ├── pipeline.py
│   └── utils.py
├── prompts/
│   ├── extraction.txt
│   ├── validation_gate.txt
│   └── ticket_writer.txt
├── inputs/                    # Sample messy texts
├── fixtures/                  # Official test cases
├── outputs/
├── app.py                     # Streamlit UI
├── main.py                    # CLI entrypoint
├── evaluate.py                # Fixture runner
├── .env
└── README.md
```

---

## Success Metrics (What Judges Care About)

1. **No invention** — every requirement is traceable to source text
2. **Rejection quality** — correctly catches vague / planted defects
3. **Actionability** — tickets can be implemented without further questions
4. **Structure** — clean, consistent ticket format
5. **Bonus impact** — tracker integration or developer-agent verification

---

## Quick Start (Once Code is Ready)

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run CLI
python main.py --text "Make the dashboard faster and add dark mode"

# Run UI
streamlit run app.py

# Evaluate fixtures
python evaluate.py --fixtures ./fixtures/
```

---

## Timeline Suggestion (24–48h Hackathon)

| Hours   | Focus                                      |
|---------|--------------------------------------------|
| 0–3     | Schema + first working Extraction+Gate     |
| 3–8     | Validation gates + ticket generation       |
| 8–14    | Full pipeline + sample testing             |
| 14–18   | Fixtures + evaluation harness              |
| 18–22   | Bonus feature + Streamlit UI               |
| 22–24   | Demo polish + submission                   |

---

## Design Principles

- **Gates over generation** — better to reject than to invent
- **Traceability first** — every claim must quote the source
- **Vertical slices** — each ticket should be independently implementable
- **Visible reasoning** — show intermediate steps in the demo
- **Automation** — human only intervenes when clarification is truly needed

---

**This is a Planning-stage AI-SDLC system.**  
The quality of the tickets it produces directly determines how well downstream coding agents (or humans) can execute.