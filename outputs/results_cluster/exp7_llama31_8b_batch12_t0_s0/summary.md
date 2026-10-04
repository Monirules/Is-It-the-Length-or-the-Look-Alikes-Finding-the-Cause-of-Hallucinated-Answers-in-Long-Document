# Official scoring: llama31_8b (bfloat16), exp7, batch12 prompt, T=0, 20 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 100.0% [95.4, 100.0] (80/80) | 90.0% [81.5, 94.8] (72/80) | 95.0% [90.4, 97.4] (152/160) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 95.0% [90.4, 97.4] (152/160)

## Where the made-up answers came from

Copied the look-alike record's value: 87.5% [81.3, 91.8] (133/152)

| source | count |
|---|---|
| lookalike | 133 |
| other_record | 19 |

## Questions with an answer

Correct: 88.8% [80.0, 94.0] (71/80)  
Wrongly refused: 1.2% [0.2, 6.7] (1/80)  
Wrong value: 10.0% [5.2, 18.5] (8/80)  
Other: 0.0% [0.0, 4.6] (0/80)

## Health checks

- labels: {'made_up': 152, 'correct': 71, 'wrong': 8, 'refused': 8, 'wrong_refusal': 1}
- three-way outcome (plan): {'made_up': 160, 'correct': 79, 'other': 1}
- answer part taken from: {'first_sentence': 240}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
