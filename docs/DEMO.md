# Demo script

Open http://localhost:8501. Click **Event sample** in the sidebar. That loads the project document below. Leave it there for all three passes.

## Project document

```
# Event director console

The director event listing shows events for the signed-in director.

## In scope

- On the director event listing, a signed-in director can export the last 30 days of events as CSV with the columns event name, start date, and status.
- The event card shows the player count.

## Already decided

- The product does not auto-close registration. Registration stays open.
- After 32 players have joined, the event card shows a warning banner and the player count.

## Out of scope

- Dark mode is out of scope.
- "Make it faster" is out of scope unless the request states a measurable target.
- "Improve the UX" is not a requirement.
```

The document can reject a contradiction or an out-of-scope line. It must not be copied into a vague ticket to fill a missing detail.

## Pass 1 — a vague line is stopped

Paste:

```
Make the dashboard faster and add dark mode.
```

Click **Process**.

Say: both asks are blocked. "Faster" has no number. Dark mode is listed as out of scope. Nothing is ready, so nothing can go to Jira.

The log under **What just ran**, and the file in `logs/`, should read in this order: orchestrator, extraction, traceability, validation, gatekeeper, ticket writer, traceability, developer, ordering.

## Pass 2 — one real ask, one vague ask, one question

Clear the text box and paste:

```
Hey team — on the director event listing, add a CSV export of the last 30 days of events. Also please improve the UX while you are in there. Thanks, Davis
```

Click **Process**.

What to point at:

- "Improve the UX" is rejected. The quote is the reason. The project document also says that phrase is not a requirement.
- The CSV is a real ask, but the paste never names the columns. The document knows the columns. The gate must ask instead of copying them.

When the page asks a question like "Which columns should the CSV include?", type:

```
Event name, start date, and status.
```

Click **Use these answers**. The agents run again only after that click.

The second run can then produce one ready ticket. Open **Tickets**. Rank 1 is the CSV. Click **Add ready tickets to the project document** and show the new section in the sidebar. That section is now in scope for a later run.

## Pass 3 — a disagreement is not resolved by the model

Clear the text box and paste:

```
Priya: Registration should auto-close when 32 players have joined.
Omar: No auto-close — leave it open and just show a warning banner after 32.
Priya: We still need the count on the event card.
```

Click **Process**.

What to point at:

- Auto-close contradicts "The product does not auto-close registration." That ask is rejected. The model does not pick Priya or Omar.
- The player count is in the request and in scope, so it can become a ready ticket.
- The banner may come back as a question because the paste does not say where it appears.

If it asks where the banner goes, type:

```
On the event card, above the player count.
```

Click **Use these answers**.

Do not create a Jira issue unless you want to show the confirm checkbox. The button stays off until a ticket is ticked and **I confirm these tickets should be created in Jira** is checked.
