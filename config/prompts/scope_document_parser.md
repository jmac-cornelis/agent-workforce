You are given a technical scoping document for a Cornelis Networks feature.  Parse it into a structured JSON object with this schema:

```json
{
  "feature_name": "short name",
  "summary": "executive summary",
  "firmware_items": [ { "title": "...", "description": "...", "category": "firmware", "complexity": "S|M|L|XL", "confidence": "high|medium|low", "dependencies": [], "rationale": "...", "acceptance_criteria": ["..."] } ],
  "driver_items": [ ... ],
  "tool_items": [ ... ],
  "test_items": [ ... ],
  "integration_items": [ ... ],
  "documentation_items": [ ... ],
  "open_questions": [ { "question": "...", "context": "...", "options": [], "blocking": false } ],
  "assumptions": [ "..." ]
}
```

Rules:
- Assign each work item to the most appropriate category.
- If the document mentions complexity/size, map it to S/M/L/XL.
- If the document mentions confidence, map it to high/medium/low.
- If not stated, default complexity to M and confidence to medium.
- Extract acceptance criteria from the text where possible.
- Identify dependencies between items by title.
- List any open questions or unknowns.
- List any assumptions made.

Return ONLY the JSON object, no other text.
