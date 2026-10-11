# Official scoring: qwen3_30b_a3b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 1.7% [0.5, 5.9] (2/120) | 0.8% [0.2, 3.0] (2/240) |
| weak | 1.7% [0.5, 5.9] (2/120) | 16.7% [11.1, 24.3] (20/120) | 9.2% [6.1, 13.5] (22/240) |
| medium | 30.8% [23.3, 39.6] (37/120) | 35.8% [27.8, 44.7] (43/120) | 33.3% [27.7, 39.5] (80/240) |
| strong | 97.5% [92.9, 99.1] (117/120) | 69.2% [60.4, 76.7] (83/120) | 83.3% [78.1, 87.5] (200/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.8% [0.2, 3.0] (2/240), weak 9.2% [6.1, 13.5] (22/240), medium 34.2% [28.5, 40.4] (82/240), strong 85.0% [79.9, 89.0] (204/240)

## Where the made-up answers came from

Copied the look-alike record's value: 95.1% [92.0, 97.0] (289/304)

| source | count |
|---|---|
| lookalike | 289 |
| other_record | 11 |
| not_in_document | 4 |

## Questions with an answer

Correct: 99.4% [98.2, 99.8] (477/480)  
Wrongly refused: 0.6% [0.2, 1.8] (3/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 477, 'refused': 651, 'made_up': 304, 'other': 5, 'wrong_refusal': 3}
- three-way outcome (plan): {'correct': 1128, 'made_up': 304, 'other': 8}
- answer part taken from: {'first_sentence': 1273, 'conclusion': 167}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 0
- empty responses: 0
