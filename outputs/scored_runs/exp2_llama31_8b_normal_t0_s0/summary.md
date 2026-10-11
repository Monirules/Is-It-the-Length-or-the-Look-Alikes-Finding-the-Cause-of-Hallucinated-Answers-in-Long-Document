# Official scoring: llama31_8b (bfloat16), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.8% [0.1, 4.6] (1/120) | 0.4% [0.1, 2.3] (1/240) |
| weak | 0.8% [0.1, 4.6] (1/120) | 0.8% [0.1, 4.6] (1/120) | 0.8% [0.2, 3.0] (2/240) |
| medium | 24.2% [17.4, 32.6] (29/120) | 5.0% [2.3, 10.5] (6/120) | 14.6% [10.7, 19.6] (35/240) |
| strong | 91.7% [85.3, 95.4] (110/120) | 37.5% [29.4, 46.4] (45/120) | 64.6% [58.3, 70.4] (155/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), weak 0.8% [0.2, 3.0] (2/240), medium 15.0% [11.0, 20.1] (36/240), strong 65.0% [58.8, 70.8] (156/240)

## Where the made-up answers came from

Copied the look-alike record's value: 97.9% [94.8, 99.2] (189/193)

| source | count |
|---|---|
| lookalike | 189 |
| other_record | 4 |

## Questions with an answer

Correct: 80.8% [77.1, 84.1] (388/480)  
Wrongly refused: 17.5% [14.4, 21.2] (84/480)  
Wrong value: 0.8% [0.3, 2.1] (4/480)  
Other: 0.8% [0.3, 2.1] (4/480)

## Health checks

- labels: {'correct': 388, 'refused': 766, 'other': 5, 'made_up': 193, 'wrong_refusal': 84, 'wrong': 4}
- three-way outcome (plan): {'correct': 1154, 'other': 89, 'made_up': 197}
- answer part taken from: {'first_sentence': 1440}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
