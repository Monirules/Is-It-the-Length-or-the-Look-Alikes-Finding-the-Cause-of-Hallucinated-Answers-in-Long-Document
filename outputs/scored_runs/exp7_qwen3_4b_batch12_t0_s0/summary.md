# Official scoring: qwen3_4b (bfloat16), exp7, batch12 prompt, T=0, 20 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 95.0% [87.8, 98.0] (76/80) | 56.2% [45.3, 66.6] (45/80) | 75.6% [68.4, 81.6] (121/160) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 75.6% [68.4, 81.6] (121/160)

## Where the made-up answers came from

Copied the look-alike record's value: 95.0% [89.6, 97.7] (115/121)

| source | count |
|---|---|
| lookalike | 115 |
| other_record | 6 |

## Questions with an answer

Correct: 78.8% [68.6, 86.3] (63/80)  
Wrongly refused: 8.8% [4.3, 17.0] (7/80)  
Wrong value: 3.8% [1.3, 10.5] (3/80)  
Other: 8.8% [4.3, 17.0] (7/80)

## Health checks

- labels: {'made_up': 121, 'correct': 63, 'wrong': 3, 'refused': 29, 'other': 17, 'wrong_refusal': 7}
- three-way outcome (plan): {'made_up': 124, 'correct': 92, 'other': 24}
- answer part taken from: {'first_sentence': 240}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
