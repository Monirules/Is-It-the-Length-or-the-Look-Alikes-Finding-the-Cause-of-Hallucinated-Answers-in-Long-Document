# Official scoring: glm45_air (fp8), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.8% [0.1, 4.6] (1/120) | 0.4% [0.1, 2.3] (1/240) |
| weak | 4.2% [1.8, 9.4] (5/120) | 16.7% [11.1, 24.3] (20/120) | 10.4% [7.2, 14.9] (25/240) |
| medium | 9.2% [5.2, 15.7] (11/120) | 39.2% [30.9, 48.1] (47/120) | 24.2% [19.2, 30.0] (58/240) |
| strong | 100.0% [96.9, 100.0] (120/120) | 86.7% [79.4, 91.6] (104/120) | 93.3% [89.4, 95.9] (224/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), weak 10.4% [7.2, 14.9] (25/240), medium 24.2% [19.2, 30.0] (58/240), strong 93.3% [89.4, 95.9] (224/240)

## Where the made-up answers came from

Copied the look-alike record's value: 93.8% [90.6, 96.0] (289/308)

| source | count |
|---|---|
| lookalike | 289 |
| other_record | 17 |
| not_in_document | 2 |

## Questions with an answer

Correct: 100.0% [99.2, 100.0] (480/480)  
Wrongly refused: 0.0% [0.0, 0.8] (0/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 480, 'refused': 651, 'made_up': 308, 'other': 1}
- three-way outcome (plan): {'correct': 1131, 'made_up': 308, 'other': 1}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
