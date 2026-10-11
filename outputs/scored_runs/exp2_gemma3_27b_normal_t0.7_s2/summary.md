# Official scoring: gemma3_27b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 5.0% [2.3, 10.5] (6/120) | 4.2% [1.8, 9.4] (5/120) | 4.6% [2.6, 8.0] (11/240) |
| weak | 21.7% [15.2, 29.9] (26/120) | 22.5% [15.9, 30.8] (27/120) | 22.1% [17.3, 27.7] (53/240) |
| medium | 98.3% [94.1, 99.5] (118/120) | 42.5% [34.0, 51.4] (51/120) | 70.4% [64.4, 75.8] (169/240) |
| strong | 99.2% [95.4, 99.9] (119/120) | 83.3% [75.7, 88.9] (100/120) | 91.2% [87.0, 94.2] (219/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 4.6% [2.6, 8.0] (11/240), weak 31.7% [26.1, 37.8] (76/240), medium 82.1% [76.7, 86.4] (197/240), strong 93.3% [89.4, 95.9] (224/240)

## Where the made-up answers came from

Copied the look-alike record's value: 58.6% [54.0, 63.1] (265/452)

| source | count |
|---|---|
| lookalike | 265 |
| other_record | 171 |
| not_in_document | 16 |

## Questions with an answer

Correct: 79.2% [75.3, 82.6] (380/480)  
Wrongly refused: 3.5% [2.2, 5.6] (17/480)  
Wrong value: 17.3% [14.2, 20.9] (83/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'wrong': 83, 'refused': 507, 'correct': 380, 'made_up': 452, 'wrong_refusal': 17, 'other': 1}
- three-way outcome (plan): {'made_up': 535, 'correct': 887, 'other': 18}
- answer part taken from: {'first_sentence': 1411, 'conclusion': 29}
- refused first, then gave a value anyway: 2
- truncated at max_tokens: 0
- empty responses: 0
