# Official scoring: llama33_70b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.8% [0.1, 4.6] (1/120) | 1.7% [0.5, 5.9] (2/120) | 1.2% [0.4, 3.6] (3/240) |
| weak | 3.3% [1.3, 8.3] (4/120) | 12.5% [7.7, 19.6] (15/120) | 7.9% [5.1, 12.0] (19/240) |
| medium | 40.0% [31.7, 48.9] (48/120) | 39.2% [30.9, 48.1] (47/120) | 39.6% [33.6, 45.9] (95/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 91.7% [85.3, 95.4] (110/120) | 95.8% [92.5, 97.7] (230/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.2% [0.4, 3.6] (3/240), weak 11.2% [7.8, 15.9] (27/240), medium 63.3% [57.1, 69.2] (152/240), strong 97.1% [94.1, 98.6] (233/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.2% [91.3, 96.2] (327/347)

| source | count |
|---|---|
| lookalike | 327 |
| other_record | 20 |

## Questions with an answer

Correct: 97.3% [95.4, 98.4] (467/480)  
Wrongly refused: 0.8% [0.3, 2.1] (4/480)  
Wrong value: 1.2% [0.6, 2.7] (6/480)  
Other: 0.6% [0.2, 1.8] (3/480)

## Health checks

- labels: {'correct': 467, 'refused': 611, 'made_up': 347, 'wrong': 6, 'other': 5, 'wrong_refusal': 4}
- three-way outcome (plan): {'correct': 1078, 'made_up': 353, 'other': 9}
- answer part taken from: {'first_sentence': 1438, 'conclusion': 2}
- refused first, then gave a value anyway: 23
- truncated at max_tokens: 3
- empty responses: 0
