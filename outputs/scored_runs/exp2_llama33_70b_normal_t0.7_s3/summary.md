# Official scoring: llama33_70b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.8% [0.1, 4.6] (1/120) | 0.0% [0.0, 3.1] (0/120) | 0.4% [0.1, 2.3] (1/240) |
| weak | 2.5% [0.9, 7.1] (3/120) | 13.3% [8.4, 20.6] (16/120) | 7.9% [5.1, 12.0] (19/240) |
| medium | 50.8% [42.0, 59.6] (61/120) | 41.7% [33.2, 50.6] (50/120) | 46.2% [40.1, 52.6] (111/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 88.3% [81.4, 92.9] (106/120) | 94.2% [90.4, 96.5] (226/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), weak 12.9% [9.3, 17.8] (31/240), medium 64.6% [58.3, 70.4] (155/240), strong 94.6% [91.0, 96.8] (227/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.4% [91.5, 96.3] (337/357)

| source | count |
|---|---|
| lookalike | 337 |
| other_record | 20 |

## Questions with an answer

Correct: 97.3% [95.4, 98.4] (467/480)  
Wrongly refused: 0.6% [0.2, 1.8] (3/480)  
Wrong value: 1.2% [0.6, 2.7] (6/480)  
Other: 0.8% [0.3, 2.1] (4/480)

## Health checks

- labels: {'correct': 467, 'refused': 600, 'made_up': 357, 'wrong': 6, 'wrong_refusal': 3, 'other': 7}
- three-way outcome (plan): {'correct': 1067, 'made_up': 363, 'other': 10}
- answer part taken from: {'first_sentence': 1439, 'conclusion': 1}
- refused first, then gave a value anyway: 29
- truncated at max_tokens: 2
- empty responses: 0
