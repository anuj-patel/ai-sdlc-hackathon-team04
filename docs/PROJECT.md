# Vague requirements → verifiable tickets

This is the project description used for validation. When this document is attached, the validation gate must judge a request against these sentences, and any quote it cites from this document must appear here verbatim.

## What this project is

This project is a planning-stage gate. A person pastes a transcript, an email, or a one-liner. Separate agents extract only what the text actually says, reject anything vague or invented, and write a ticket only when a developer could implement it without guessing.

The orchestrator does not write tickets. It runs extraction, traceability, validation, a vague-language gate, ticket writing, a developer check, and ordering. Traceability runs again after the ticket writer. Ordering sets rank and priority. The page shows rank and priority. It does not show the scoring formula.

## What the system accepts

- The requirement text may be a meeting transcript, an email, or a short one-liner.
- A project document may be attached. This file is that document for this system.
- A GitHub repository URL may be attached. The repository README is read and treated as a project document.
- The command line, `POST /process`, and the Streamlit page all run the same orchestrator.

## What a ready ticket must contain

- A ready ticket has a title, a problem, a user, a context, a description, testable acceptance criteria, a priority, a rank, a type, and exact source quotes.
- Priority is high, medium, or low. Type is feature, bug, chore, or improvement.
- Status is ready, needs_clarification, or rejected.
- Every source quote is an exact excerpt of the requirement text. A quote that is not in the requirement text is an invented requirement and is rejected.

## What the system rejects

- It rejects vague language such as "make it better", "improve UX", and "faster" when the text states no measurable outcome.
- It rejects a requirement that is not present in the source text.
- It rejects an internal contradiction instead of choosing a side.
- It does not skip the validation gate, and it does not create a ready ticket for a sentence that is vague or unsupported.
- It does not invent actors, metrics, or features that the source text does not state.
- It does not copy extra detail from this document into a ticket to make a vague request look ready.
- It does not write product code. It does not create a tracker issue until the user confirms on the page.

## In scope for this project

- The Streamlit UI shows each rejected requirement with its exact source quote and the reason for rejection.
- The Streamlit UI shows each subagent step. The step list is stored in a log file and is left out of the JSON download.
- The Streamlit UI can load a GitHub repository README into the project document used for validation.
- The Streamlit UI can add the ready tickets into the project document. That section is replaced when the user adds them again. The rest of the document stays.
- The CLI accepts `--text` or `--input`, plus optional `--context` and `--repo`.

## Out of scope when this document is the validation context

- Requests to build features for a different product, such as a dashboard theme or an event export, are out of scope when this document is the validation context.
- Dark mode and performance tuning are out of scope unless a later document adds them.
- Creating a tracker issue without the user confirming on the page is out of scope.

## How validation must use this document

- When this document is present, a request that contradicts a sentence above is rejected, and the decision quotes both the request and this document.
- When this document is present, a request that asks for work listed as out of scope is rejected, and the decision quotes the out-of-scope sentence.
- When this document is absent, judge the request only against itself.
- A specific request that this document already lists as in scope may become a ready ticket, using quotes from the request, not invented behavior.
