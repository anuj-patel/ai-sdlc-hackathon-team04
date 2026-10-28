# Validation subagent

Read [prompts/validation_gate.txt](../../../prompts/validation_gate.txt) and follow it.

Input: the requirement text, the project document (this may be a GitHub README), and the candidates that survived traceability.

Use the project document only to reject contradictions and out-of-scope asks. Do not fill missing actor, metric, or behavior from that document.

When a decision depends on the document, `context_quotes` must be exact substrings of it. `source_quotes` must be exact substrings of the requirement text.

Return one result per candidate:

```json
{
  "results": [
    {
      "requirement_id": "REQ-1",
      "decision": "ready",
      "reasons": ["short reason"],
      "clarification_questions": [],
      "source_quotes": ["exact quote from the requirement"],
      "context_quotes": []
    }
  ]
}
```

`decision` is `ready`, `needs_clarification`, or `rejected`.
