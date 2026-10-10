# Official scoring: qwen3_next_80b (fp8), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 62.5% [53.6, 70.6] (75/120) | 45.0% [36.4, 53.9] (54/120) | 53.8% [47.4, 59.9] (129/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 54.2% [47.8, 60.4] (130/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.4% [94.5, 99.6] (127/129)

| source | count |
|---|---|
| lookalike | 127 |
| other_record | 2 |

## Questions with an answer

Correct: 95.0% [89.5, 97.7] (114/120)  
Wrongly refused: 4.2% [1.8, 9.4] (5/120)  
Wrong value: 0.8% [0.1, 4.6] (1/120)  
Other: 0.0% [0.0, 3.1] (0/120)

## Health checks

- labels: {'correct': 114, 'refused': 111, 'made_up': 129, 'wrong_refusal': 5, 'wrong': 1}
- three-way outcome (plan): {'correct': 225, 'made_up': 130, 'other': 5}
- answer part taken from: {'first_sentence': 358, 'final_line': 1, 'conclusion': 1}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
