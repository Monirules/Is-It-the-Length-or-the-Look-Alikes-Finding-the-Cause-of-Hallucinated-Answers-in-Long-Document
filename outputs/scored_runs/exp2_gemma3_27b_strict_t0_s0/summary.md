# Official scoring: gemma3_27b (bfloat16), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 99.2% [95.4, 99.9] (119/120) | 56.7% [47.7, 65.2] (68/120) | 77.9% [72.3, 82.7] (187/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 77.9% [72.3, 82.7] (187/240)

## Where the made-up answers came from

Copied the look-alike record's value: 59.9% [52.7, 66.7] (112/187)

| source | count |
|---|---|
| lookalike | 112 |
| other_record | 67 |
| not_in_document | 8 |

## Questions with an answer

Correct: 70.0% [61.3, 77.5] (84/120)  
Wrongly refused: 14.2% [9.0, 21.5] (17/120)  
Wrong value: 15.8% [10.4, 23.4] (19/120)  
Other: 0.0% [0.0, 3.1] (0/120)

## Health checks

- labels: {'correct': 84, 'made_up': 187, 'wrong': 19, 'refused': 53, 'wrong_refusal': 17}
- three-way outcome (plan): {'correct': 137, 'made_up': 206, 'other': 17}
- answer part taken from: {'first_sentence': 360}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 1
- empty responses: 0
