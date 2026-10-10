# Official scoring: qwen3_30b_a3b (bfloat16), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 3.3% [1.3, 8.3] (4/120) | 1.7% [0.6, 4.2] (4/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 19.2% [13.1, 27.1] (23/120) | 9.6% [6.5, 14.0] (23/240) |
| medium | 26.7% [19.6, 35.2] (32/120) | 25.0% [18.1, 33.4] (30/120) | 25.8% [20.7, 31.7] (62/240) |
| strong | 98.3% [94.1, 99.5] (118/120) | 67.5% [58.7, 75.2] (81/120) | 82.9% [77.6, 87.2] (199/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.7% [0.6, 4.2] (4/240), weak 9.6% [6.5, 14.0] (23/240), medium 26.2% [21.1, 32.2] (63/240), strong 83.3% [78.1, 87.5] (200/240)

## Where the made-up answers came from

Copied the look-alike record's value: 95.8% [92.9, 97.6] (276/288)

| source | count |
|---|---|
| lookalike | 276 |
| other_record | 9 |
| not_in_document | 3 |

## Questions with an answer

Correct: 99.6% [98.5, 99.9] (478/480)  
Wrongly refused: 0.4% [0.1, 1.5] (2/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 478, 'refused': 666, 'made_up': 288, 'other': 6, 'wrong_refusal': 2}
- three-way outcome (plan): {'correct': 1144, 'made_up': 288, 'other': 8}
- answer part taken from: {'first_sentence': 1265, 'conclusion': 175}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
