# Official scoring: qwen3_30b_a3b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.8% [0.1, 4.6] (1/120) | 0.4% [0.1, 2.3] (1/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 20.0% [13.8, 28.0] (24/120) | 10.0% [6.8, 14.4] (24/240) |
| medium | 30.0% [22.5, 38.7] (36/120) | 30.0% [22.5, 38.7] (36/120) | 30.0% [24.6, 36.1] (72/240) |
| strong | 97.5% [92.9, 99.1] (117/120) | 68.3% [59.6, 76.0] (82/120) | 82.9% [77.6, 87.2] (199/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), weak 10.0% [6.8, 14.4] (24/240), medium 30.0% [24.6, 36.1] (72/240), strong 85.4% [80.4, 89.3] (205/240)

## Where the made-up answers came from

Copied the look-alike record's value: 96.3% [93.5, 97.9] (285/296)

| source | count |
|---|---|
| lookalike | 285 |
| other_record | 9 |
| not_in_document | 2 |

## Questions with an answer

Correct: 99.2% [97.9, 99.7] (476/480)  
Wrongly refused: 0.8% [0.3, 2.1] (4/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 476, 'refused': 661, 'made_up': 296, 'wrong_refusal': 4, 'other': 3}
- three-way outcome (plan): {'correct': 1137, 'made_up': 296, 'other': 7}
- answer part taken from: {'first_sentence': 1300, 'conclusion': 140}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
