# Developer-agent check

This stage is a checklist, not a new feature pass. Apply it after ticket quotes have been checked.

A ticket passes only when a developer or a coding agent could implement it from the ticket alone:

- `user` is an exact phrase from the source
- `context` (screen, API, or data) is an exact phrase from the source
- `problem` is stated
- at least one acceptance criterion is specific enough to test, and it is not vague language
- a source quote is attached
- no clarification question is still open

If any item fails, do not leave the ticket ready. Return it as `needs_clarification` with the missing questions. Do not invent the user, the context, or the success check.
