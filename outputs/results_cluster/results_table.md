# Results table (official scoring, score-v1)

One row per condition. **Made up** = share of questions with no answer where the model committed to a value (95% Wilson interval). **Copied** = made-up answers that copied the look-alike record's value. **Mentions** = refusals that still quoted the look-alike's value (a strict reading would count them as made up). **Correct** = questions with an answer answered correctly.

| prompt_style | ladder | made up | copied | mentions | correct (with answer) | wrongly refused |
|---|---|---|---|---|---|---|
| batch12 | name | 100.0% [95.4, 100.0] (80/80) | 68/80 | 0 | 87.5% [73.9, 94.5] (35/40) | 0/40 |
| batch12 | role | 90.0% [81.5, 94.8] (72/80) | 65/72 | 0 | 90.0% [76.9, 96.0] (36/40) | 1/40 |
| normal | name | 87.5% [78.5, 93.1] (70/80) | 70/70 | 0 | 95.0% [83.5, 98.6] (38/40) | 1/40 |
| normal | role | 27.5% [18.9, 38.1] (22/80) | 21/22 | 0 | 60.0% [44.6, 73.7] (24/40) | 15/40 |
