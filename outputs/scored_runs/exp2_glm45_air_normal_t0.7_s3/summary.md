# Official scoring: glm45_air (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 1.7% [0.5, 5.9] (2/120) | 0.8% [0.2, 3.0] (2/240) |
| weak | 4.2% [1.8, 9.4] (5/120) | 17.5% [11.7, 25.3] (21/120) | 10.8% [7.5, 15.4] (26/240) |
| medium | 11.7% [7.1, 18.6] (14/120) | 32.5% [24.8, 41.3] (39/120) | 22.1% [17.3, 27.7] (53/240) |
| strong | 99.2% [95.4, 99.9] (119/120) | 80.8% [72.9, 86.9] (97/120) | 90.0% [85.6, 93.2] (216/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.8% [0.2, 3.0] (2/240), weak 10.8% [7.5, 15.4] (26/240), medium 22.1% [17.3, 27.7] (53/240), strong 90.0% [85.6, 93.2] (216/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.9% [91.8, 96.9] (282/297)

| source | count |
|---|---|
| lookalike | 282 |
| other_record | 13 |
| not_in_document | 2 |

## Questions with an answer

Correct: 99.2% [97.9, 99.7] (476/480)  
Wrongly refused: 0.8% [0.3, 2.1] (4/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 476, 'refused': 657, 'made_up': 297, 'wrong_refusal': 4, 'other': 6}
- three-way outcome (plan): {'correct': 1133, 'made_up': 297, 'other': 10}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
