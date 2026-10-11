# Official scoring: glm45_air (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.8% [0.1, 4.6] (1/120) | 2.5% [0.9, 7.1] (3/120) | 1.7% [0.6, 4.2] (4/240) |
| weak | 5.8% [2.9, 11.6] (7/120) | 17.5% [11.7, 25.3] (21/120) | 11.7% [8.2, 16.3] (28/240) |
| medium | 8.3% [4.6, 14.7] (10/120) | 45.8% [37.2, 54.7] (55/120) | 27.1% [21.9, 33.0] (65/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 84.2% [76.6, 89.6] (101/120) | 92.1% [88.0, 94.9] (221/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.7% [0.6, 4.2] (4/240), weak 11.7% [8.2, 16.3] (28/240), medium 27.1% [21.9, 33.0] (65/240), strong 92.1% [88.0, 94.9] (221/240)

## Where the made-up answers came from

Copied the look-alike record's value: 92.8% [89.4, 95.1] (295/318)

| source | count |
|---|---|
| lookalike | 295 |
| other_record | 18 |
| not_in_document | 5 |

## Questions with an answer

Correct: 99.6% [98.5, 99.9] (478/480)  
Wrongly refused: 0.2% [0.0, 1.2] (1/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.2% [0.0, 1.2] (1/480)

## Health checks

- labels: {'correct': 478, 'refused': 636, 'made_up': 318, 'wrong_refusal': 1, 'other': 7}
- three-way outcome (plan): {'correct': 1114, 'made_up': 318, 'other': 8}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
