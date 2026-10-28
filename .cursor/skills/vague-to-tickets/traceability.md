# Traceability

This stage does not use a model.

A quote is valid only when it is a substring of its source, ignoring extra whitespace. Otherwise it is invented.

- On candidates: reject the candidate when none of its `source_quotes` appear in the requirement text. Reason: `quote not found in source`.
- On gate results: drop any `context_quotes` entry that does not appear in the project document. Add the reason `Dropped context quotes that are not in the project document.`
- On tickets: drop a ticket when none of its `source_quotes` appear in the requirement text, or when `acceptance_criteria` is empty.

The same rules are implemented in `src/agents/traceability.py`. Prefer that module over re-deciding by eye when the Python pipeline is available.
