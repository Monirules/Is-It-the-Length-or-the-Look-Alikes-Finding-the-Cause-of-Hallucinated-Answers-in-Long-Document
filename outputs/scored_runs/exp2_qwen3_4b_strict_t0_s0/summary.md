# Official scoring: qwen3_4b (bfloat16), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 61.7% [52.7, 69.9] (74/120) | 37.5% [29.4, 46.4] (45/120) | 49.6% [43.3, 55.9] (119/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 51.2% [45.0, 57.5] (123/240)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [96.9, 100.0] (119/119)

| source | count |
|---|---|
| lookalike | 119 |

## Questions with an answer

Correct: 90.0% [83.3, 94.2] (108/120)  
Wrongly refused: 10.0% [5.8, 16.7] (12/120)  
Wrong value: 0.0% [0.0, 3.1] (0/120)  
Other: 0.0% [0.0, 3.1] (0/120)

## Health checks

- labels: {'correct': 108, 'made_up': 119, 'refused': 120, 'wrong_refusal': 12, 'other': 1}
- three-way outcome (plan): {'correct': 228, 'made_up': 119, 'other': 13}
- answer part taken from: {'first_sentence': 345, 'final_line': 9, 'conclusion': 6}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 1
- empty responses: 0
