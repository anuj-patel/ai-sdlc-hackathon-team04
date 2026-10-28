# Extraction subagent

Read [prompts/extraction.txt](../../../prompts/extraction.txt) and follow it.

Input: the requirement text only. Do not receive the project document or the GitHub README. Context from those files is not a requirement.

Return JSON:

```json
{
  "candidates": [
    {
      "id": "REQ-1",
      "statement": "one atomic ask, faithful to the quote",
      "source_quotes": ["exact substring of the requirement text"],
      "actor": null,
      "context": null,
      "success_metric": null
    }
  ]
}
```

Return no other commentary. If the text is empty or noise, return `{"candidates": []}`.
