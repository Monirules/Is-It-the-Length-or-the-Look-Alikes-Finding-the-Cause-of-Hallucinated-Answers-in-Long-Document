# Official scoring: llama33_70b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.8% [0.1, 4.6] (1/120) | 2.5% [0.9, 7.1] (3/120) | 1.7% [0.6, 4.2] (4/240) |
| weak | 1.7% [0.5, 5.9] (2/120) | 15.8% [10.4, 23.4] (19/120) | 8.8% [5.8, 13.0] (21/240) |
| medium | 46.7% [38.0, 55.6] (56/120) | 39.2% [30.9, 48.1] (47/120) | 42.9% [36.8, 49.2] (103/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 92.5% [86.4, 96.0] (111/120) | 96.2% [93.0, 98.0] (231/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.7% [0.6, 4.2] (4/240), weak 12.1% [8.5, 16.8] (29/240), medium 63.7% [57.5, 69.6] (153/240), strong 97.5% [94.7, 98.8] (234/240)

## Where the made-up answers came from

Copied the look-alike record's value: 93.0% [89.9, 95.2] (334/359)

| source | count |
|---|---|
| lookalike | 334 |
| other_record | 25 |

## Questions with an answer

Correct: 97.1% [95.2, 98.3] (466/480)  
Wrongly refused: 0.4% [0.1, 1.5] (2/480)  
Wrong value: 1.7% [0.8, 3.3] (8/480)  
Other: 0.8% [0.3, 2.1] (4/480)

## Health checks

- labels: {'correct': 466, 'refused': 599, 'made_up': 359, 'wrong': 8, 'other': 6, 'wrong_refusal': 2}
- three-way outcome (plan): {'correct': 1065, 'made_up': 367, 'other': 8}
- answer part taken from: {'first_sentence': 1438, 'conclusion': 2}
- refused first, then gave a value anyway: 31
- truncated at max_tokens: 1
- empty responses: 0
