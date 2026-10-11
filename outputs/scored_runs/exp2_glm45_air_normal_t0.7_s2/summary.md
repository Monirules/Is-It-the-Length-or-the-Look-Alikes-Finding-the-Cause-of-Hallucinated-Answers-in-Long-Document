# Official scoring: glm45_air (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 2.5% [0.9, 7.1] (3/120) | 1.2% [0.4, 3.6] (3/240) |
| weak | 8.3% [4.6, 14.7] (10/120) | 20.8% [14.5, 28.9] (25/120) | 14.6% [10.7, 19.6] (35/240) |
| medium | 6.7% [3.4, 12.6] (8/120) | 32.5% [24.8, 41.3] (39/120) | 19.6% [15.1, 25.1] (47/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 82.5% [74.7, 88.3] (99/120) | 91.2% [87.0, 94.2] (219/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.2% [0.4, 3.6] (3/240), weak 14.6% [10.7, 19.6] (35/240), medium 19.6% [15.1, 25.1] (47/240), strong 91.2% [87.0, 94.2] (219/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.1% [90.8, 96.2] (286/304)

| source | count |
|---|---|
| lookalike | 286 |
| other_record | 18 |

## Questions with an answer

Correct: 99.8% [98.8, 100.0] (479/480)  
Wrongly refused: 0.0% [0.0, 0.8] (0/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.2% [0.0, 1.2] (1/480)

## Health checks

- labels: {'correct': 479, 'refused': 647, 'made_up': 304, 'other': 10}
- three-way outcome (plan): {'correct': 1126, 'made_up': 304, 'other': 10}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
