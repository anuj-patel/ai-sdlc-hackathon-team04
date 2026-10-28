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

