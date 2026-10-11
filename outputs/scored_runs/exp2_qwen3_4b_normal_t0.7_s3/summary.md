# Official scoring: qwen3_4b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 30.0% [22.5, 38.7] (36/120) | 0.8% [0.1, 4.6] (1/120) | 15.4% [11.4, 20.5] (37/240) |
| strong | 77.5% [69.2, 84.1] (93/120) | 50.0% [41.2, 58.8] (60/120) | 63.7% [57.5, 69.6] (153/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 29.2% [23.8, 35.2] (70/240), strong 76.7% [70.9, 81.6] (184/240)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [98.0, 100.0] (190/190)

| source | count |
|---|---|
| lookalike | 190 |

## Questions with an answer

Correct: 95.0% [92.7, 96.6] (456/480)  
Wrongly refused: 4.8% [3.2, 7.1] (23/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.2% [0.0, 1.2] (1/480)

## Health checks

- labels: {'correct': 456, 'refused': 768, 'made_up': 190, 'wrong_refusal': 23, 'other': 3}
- three-way outcome (plan): {'correct': 1224, 'made_up': 190, 'other': 26}
- answer part taken from: {'first_sentence': 681, 'conclusion': 697, 'final_line': 62}
- refused first, then gave a value anyway: 25
- truncated at max_tokens: 0
- empty responses: 0
