# Official scoring: llama31_8b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.8% [0.1, 4.6] (1/120) | 0.8% [0.1, 4.6] (1/120) | 0.8% [0.2, 3.0] (2/240) |
| weak | 3.3% [1.3, 8.3] (4/120) | 4.2% [1.8, 9.4] (5/120) | 3.8% [2.0, 7.0] (9/240) |
| medium | 36.7% [28.6, 45.6] (44/120) | 9.2% [5.2, 15.7] (11/120) | 22.9% [18.1, 28.6] (55/240) |
| strong | 92.5% [86.4, 96.0] (111/120) | 45.8% [37.2, 54.7] (55/120) | 69.2% [63.1, 74.7] (166/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.8% [0.2, 3.0] (2/240), weak 7.1% [4.5, 11.0] (17/240), medium 32.5% [26.9, 38.7] (78/240), strong 71.2% [65.2, 76.6] (171/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.8% [91.2, 97.0] (220/232)

| source | count |
|---|---|
| lookalike | 220 |
| other_record | 11 |
| not_in_document | 1 |

## Questions with an answer

Correct: 82.7% [79.1, 85.8] (397/480)  
Wrongly refused: 16.0% [13.0, 19.6] (77/480)  
Wrong value: 1.0% [0.4, 2.4] (5/480)  
Other: 0.2% [0.0, 1.2] (1/480)

## Health checks

- labels: {'correct': 397, 'refused': 725, 'made_up': 232, 'wrong': 5, 'wrong_refusal': 77, 'other': 4}
- three-way outcome (plan): {'correct': 1122, 'made_up': 237, 'other': 81}
- answer part taken from: {'first_sentence': 1439, 'conclusion': 1}
- refused first, then gave a value anyway: 4
- truncated at max_tokens: 0
- empty responses: 0
