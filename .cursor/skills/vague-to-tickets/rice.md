# RICE ranking

Rank only tickets that passed the developer-agent check. This orders one batch. It does not set a company-wide priority.

Score = Reach × Impact × Confidence / Effort.

- Reach, impact, and effort are measurements only when the source states a count, an outcome size, or a duration such as "in 2 days". "Last 30 days" is a data window, not effort.
- When a factor is missing, use a labeled estimate for ordering and lower the confidence. Do not invent a headcount or a schedule.
- Impact scale: 3 massive, 2 high, 1 medium, 0.5 low, 0.25 minimal.
- Order a dependency before the ticket that needs it, even when its score is lower.
- Rank 1 is first to do. Priority is the RICE band (`high`, `medium`, `low`), separate from that sequence.
- One ticket, with no stated reach, stays `medium`.

Write the PRD from these tickets. Leave a section empty, and say it was not stated, when the source does not contain it.
