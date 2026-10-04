# Official scoring: qwen3_next_80b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 34.2% [26.3, 43.0] (41/120) | 5.8% [2.9, 11.6] (7/120) | 20.0% [15.4, 25.5] (48/240) |
| strong | 95.8% [90.6, 98.2] (115/120) | 76.7% [68.3, 83.3] (92/120) | 86.2% [81.3, 90.0] (207/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 31.7% [26.1, 37.8] (76/240), strong 90.4% [86.0, 93.5] (217/240)

## Where the made-up answers came from

Copied the look-alike record's value: 99.2% [97.2, 99.8] (253/255)

| source | count |
|---|---|
| lookalike | 253 |
| other_record | 2 |

## Questions with an answer

Correct: 99.2% [97.9, 99.7] (476/480)  
Wrongly refused: 0.6% [0.2, 1.8] (3/480)  
Wrong value: 0.2% [0.0, 1.2] (1/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 476, 'refused': 699, 'made_up': 255, 'other': 6, 'wrong_refusal': 3, 'wrong': 1}
- three-way outcome (plan): {'correct': 1175, 'made_up': 256, 'other': 9}
- answer part taken from: {'first_sentence': 1362, 'conclusion': 56, 'final_line': 22}
- refused first, then gave a value anyway: 30
- truncated at max_tokens: 0
- empty responses: 0
