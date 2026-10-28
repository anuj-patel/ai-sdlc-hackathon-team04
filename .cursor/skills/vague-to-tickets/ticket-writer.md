# Ticket writer subagent

Read [prompts/ticket_writer.txt](../../../prompts/ticket_writer.txt) and follow it.

Input: the requirement text and only the candidates whose gate decision is `ready`. Do not receive rejected candidates. Do not receive the project document.

Write no ticket when the ready list is empty. Every `source_quotes` entry must be an exact substring of the requirement text. Do not add behavior that the quote does not state.

Return:

```json
{
  "tickets": [
    {
      "id": "T-1",
      "title": "short imperative title",
      "problem": "exact phrase from the source, or empty",
      "user": "exact phrase from the source, or empty",
      "context": "exact phrase from the source, or empty",
      "description": "what to build, grounded in quotes",
      "acceptance_criteria": ["testable check"],
      "success_metric": "exact phrase from the source, or empty",
      "out_of_scope": [],
      "priority": "medium",
      "type": "feature",
      "source_quotes": ["exact quote"],
      "confidence_score": 0.8,
      "status": "ready",
      "clarification_questions": null,
      "dependencies": []
    }
  ]
}
```
