# Judgement record

This note is the evidence for the four scores: why this approach, what was built, what the first run did, and what the second run fixed.

## 1. Strength of thinking

A planning model will turn a vague sentence into a ticket that looks finished. A developer still has to guess, or the ticket contains behavior nobody said.

The approach is gates over generation.

- The orchestrator routes the work. It does not write tickets.
- A candidate is one ask pulled from the paste. It is not a ticket yet.
- Every quote must be an exact substring of the text the person pasted. A quote that is not in that text is rejected as invented.
- The project document is used only to reject a contradiction or an out-of-scope ask. It is not copied in to make a vague line look ready.
- Code can overturn the model. Vague language with no number cannot stay ready.
- Jira is created only after a person ticks the tickets and confirms. Rejected asks are never sent.

## 2. Base setup

The running system is the Python pipeline in `src/agents/orchestrator.py`. The page, `python main.py`, and `POST /process` all call it.

The Cursor skill `.cursor/skills/vague-to-tickets/SKILL.md` is the same sequence for chat when `GEMINI_API_KEY` is missing. Each brief limits what that stage can see. Extraction and the ticket writer do not receive the project document.

Stages, in order:

1. Orchestrator
2. Extraction
3. Traceability
4. Validation
5. Gatekeeper
6. Ticket writer
7. Traceability again
8. Developer check
9. Ordering

Integrations stay narrow. Gemini does extraction, validation, and ticket writing. GitHub is a README read for validation, not issue creation. Jira is a confirmed create of ready tickets only.

Output is judged in `evaluate.py`.

- `python evaluate.py --gatekeepers` checks the code rules and does not call the model.
- `python evaluate.py` runs the three fixtures through the model.

The offline check was run after the second-run fixes. All 14 checks passed: empty input stops, vague ready is blocked, a measured speed stays ready, `reject` maps to `rejected`, the developer check holds a ticket with no user, a data window such as "last 30 days" is not treated as effort, the score formula is hidden on the ticket, and adding ready tickets to the project document replaces that section instead of duplicating it.

The model-backed fixture run was not repeated after a Gemini 429. Do not claim those three fixtures passed on the second run.

## 3. First run

### What went in

| Input | What we expected |
| --- | --- |
| Empty text | Stop before any model call. |
| `inputs/clear_request.txt`: "On the settings page, the signed-in user can switch the theme between light and dark. The choice persists after reload." | Ready tickets whose quotes are in that text. |
| `fixtures/01_vague_oneliner.json`: "Make the dashboard faster and add dark mode" | No ready ticket. "faster" must not ship. Dark mode must not be invented into a theme spec. |
| `fixtures/02_email_mixed.json`: CSV of the last 30 days, plus "improve the UX" | The CSV can be ready. "improve the UX" must not be ready. |
| `fixtures/03_contradiction.json`: auto-close versus a warning banner, plus the player count on the event card | Do not pick a side on auto-close. The player count can be ready. |

### What came out

- Empty input stopped before extraction. The log says so.
- The clear settings sentence produced two ready tickets: switch the theme, and persist the choice after reload. Both quotes were in the source. The trace was extraction, traceability, validation, ticket writer, traceability.
- On the page, the contradiction paste kept the player count and held the banner. Auto-close did not become a ready ticket.

### What we found by hand

These were not theoretical. They happened on the page or in the command.

1. **The run crashed on the model's wording.** Validation returned `reject`. The gate only accepts `ready`, `needs_clarification`, or `rejected`. Pydantic stopped the run before any ticket was written: `Input should be 'ready', 'needs_clarification' or 'rejected'`.
2. **A rate limit crashed the page.** Gemini returned 429. The page only caught `RuntimeError`, so the person saw a traceback instead of an error message.
3. **The finished log was out of order.** The gatekeeper line was written before the validation line, even though validation runs first.
4. **The project document was behind the product.** `docs/PROJECT.md` still described four agents and treated tracker publishing as out of scope, while the page already had a developer check, ordering, a tracker export, and a confirmed Jira create.
5. **The ticket tried to teach the scoring formula.** Rank and priority are the result. The Reach, Impact, Confidence, and Effort breakdown was on the ticket, the PRD, and the tracker file. A person using the page should not have to understand that formula.
6. **The second demo paste, checked by hand.** With the event-director document loaded, the paste was a CSV export on the director event listing plus "improve the UX." The page returned **1 ready and 1 rejected**. The CSV was specific enough to become a ticket. "Improve the UX" was rejected. That split is the gate working. It did not ask which columns to include, because the paste already named the place and the outcome. Columns that appear on the ticket but were not in the paste would be a miss: the document must not fill that gap.

### What the first run missed

- The word `reject` was a real model output, and the app treated it as a crash instead of a decision.
- Fixture 03 says the conflict may be rejected or sent back for clarification. The eval still requires at least one rejection. That disagreement was left as it is.
- The full fixture eval through Gemini was not re-run after the 429.

## 4. Second run

Each fix below is aimed at something the first run got wrong. The proof that does not call the model is `python evaluate.py --gatekeepers`.

| What the first run did | What changed | Proof |
| --- | --- | --- |
| Crashed when the model said `reject` | `normalize_decision` maps `reject` and `fail` to `rejected`, and `pass` to `ready`. An unreadable decision becomes "needs an answer" instead of a crash. | Check `decision_aliases`: `normalize_decision("reject") == "rejected"`. |
| 429 showed a traceback | The page catches the error and shows it as a message. | `app.py` handles `Exception` around the run. |
| Log listed the gatekeeper before validation | Each step is appended when that agent finishes. The file is numbered `01`, `02`, `03` in that order. The page label for the last step is "ordering". | Empty-input log starts with `01` orchestrator, then `02`. Validation is written before the gatekeeper in `src/agents/orchestrator.py`. |
| Vague "faster" could be marked ready by the model | The gatekeeper overturns a ready decision whose quote is vague and has no number. "Faster than 200ms" stays. | Checks `vague_ready_blocked` and `measured_speed_stays_ready`. |
| A ticket could ship with no user | The developer check holds it and asks who the user is. | Check `developer_check_holds_missing_user`. The clear settings sentence passes. |
| "Last 30 days" could be read as effort | A data window is not a duration. | Check `data_window_is_not_effort`. |
| The score formula was on the ticket | The ticket, PRD, tracker CSV, and JSON download show rank and priority only. | Check `ticket_hides_score_formula`. |
| The project document could not absorb accepted work | **Add ready tickets to the project document** writes one section, "Ready tickets now in scope." Clicking again replaces that section. | Check `project_doc_takes_ready_tickets`. `docs/PROJECT.md` now matches the current stages. |

Re-running the sentence that crashed the first time should finish. "Make the dashboard faster" is rejected for vague language. It does not die on the word `reject`.
