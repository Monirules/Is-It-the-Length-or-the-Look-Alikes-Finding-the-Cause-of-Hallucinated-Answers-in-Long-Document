# Official scoring: gemma3_27b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 5.0% [2.3, 10.5] (6/120) | 4.2% [1.8, 9.4] (5/120) | 4.6% [2.6, 8.0] (11/240) |
| weak | 21.7% [15.2, 29.9] (26/120) | 22.5% [15.9, 30.8] (27/120) | 22.1% [17.3, 27.7] (53/240) |
| medium | 98.3% [94.1, 99.5] (118/120) | 44.2% [35.6, 53.1] (53/120) | 71.2% [65.2, 76.6] (171/240) |
| strong | 99.2% [95.4, 99.9] (119/120) | 82.5% [74.7, 88.3] (99/120) | 90.8% [86.5, 93.9] (218/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 4.6% [2.6, 8.0] (11/240), weak 31.2% [25.7, 37.4] (75/240), medium 81.2% [75.8, 85.7] (195/240), strong 93.3% [89.4, 95.9] (224/240)

## Where the made-up answers came from

Copied the look-alike record's value: 58.7% [54.1, 63.2] (266/453)

| source | count |
|---|---|
| lookalike | 266 |
| other_record | 172 |
| not_in_document | 15 |

## Questions with an answer

Correct: 79.2% [75.3, 82.6] (380/480)  
Wrongly refused: 3.3% [2.1, 5.3] (16/480)  
Wrong value: 17.5% [14.4, 21.2] (84/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'wrong': 84, 'refused': 506, 'correct': 380, 'made_up': 453, 'wrong_refusal': 16, 'other': 1}
- three-way outcome (plan): {'made_up': 537, 'correct': 886, 'other': 17}
- answer part taken from: {'first_sentence': 1414, 'conclusion': 26}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 0
- empty responses: 0
