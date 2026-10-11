# Official scoring: llama33_70b (fp8), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 1.7% [0.5, 5.9] (2/120) | 9.2% [5.2, 15.7] (11/120) | 5.4% [3.2, 9.0] (13/240) |
| medium | 51.7% [42.8, 60.4] (62/120) | 36.7% [28.6, 45.6] (44/120) | 44.2% [38.0, 50.5] (106/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 88.3% [81.4, 92.9] (106/120) | 94.2% [90.4, 96.5] (226/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 6.7% [4.1, 10.6] (16/240), medium 63.7% [57.5, 69.6] (153/240), strong 95.8% [92.5, 97.7] (230/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.8% [91.9, 96.7] (327/345)

| source | count |
|---|---|
| lookalike | 327 |
| other_record | 18 |

## Questions with an answer

Correct: 98.3% [96.7, 99.2] (472/480)  
Wrongly refused: 0.2% [0.0, 1.2] (1/480)  
Wrong value: 1.0% [0.4, 2.4] (5/480)  
Other: 0.4% [0.1, 1.5] (2/480)

## Health checks

- labels: {'correct': 472, 'refused': 613, 'wrong': 5, 'made_up': 345, 'other': 4, 'wrong_refusal': 1}
- three-way outcome (plan): {'correct': 1085, 'made_up': 350, 'other': 5}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 32
- truncated at max_tokens: 3
- empty responses: 0
