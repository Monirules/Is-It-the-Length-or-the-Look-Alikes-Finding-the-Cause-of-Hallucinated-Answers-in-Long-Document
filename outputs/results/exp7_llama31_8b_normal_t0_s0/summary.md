# Official scoring: llama31_8b (bfloat16), exp7, normal prompt, T=0, 20 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 87.5% [78.5, 93.1] (70/80) | 27.5% [18.9, 38.1] (22/80) | 57.5% [49.8, 64.9] (92/160) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 57.5% [49.8, 64.9] (92/160)

## Where the made-up answers came from

Copied the look-alike record's value: 98.9% [94.1, 99.8] (91/92)

| source | count |
|---|---|
| lookalike | 91 |
| other_record | 1 |

## Questions with an answer

Correct: 77.5% [67.2, 85.3] (62/80)  
Wrongly refused: 20.0% [12.7, 30.0] (16/80)  
Wrong value: 1.2% [0.2, 6.7] (1/80)  
Other: 1.2% [0.2, 6.7] (1/80)

## Health checks

- labels: {'made_up': 92, 'correct': 62, 'refused': 67, 'wrong_refusal': 16, 'other': 2, 'wrong': 1}
- three-way outcome (plan): {'made_up': 93, 'correct': 129, 'other': 18}
- answer part taken from: {'first_sentence': 239, 'conclusion': 1}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
