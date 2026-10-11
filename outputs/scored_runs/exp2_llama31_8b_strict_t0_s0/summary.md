# Official scoring: llama31_8b (bfloat16), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 81.7% [73.8, 87.6] (98/120) | 32.5% [24.8, 41.3] (39/120) | 57.1% [50.8, 63.2] (137/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 57.1% [50.8, 63.2] (137/240)

## Where the made-up answers came from

Copied the look-alike record's value: 97.8% [93.8, 99.3] (134/137)

| source | count |
|---|---|
| lookalike | 134 |
| other_record | 2 |
| not_in_document | 1 |

## Questions with an answer

Correct: 68.3% [59.6, 76.0] (82/120)  
Wrongly refused: 28.3% [21.0, 37.0] (34/120)  
Wrong value: 1.7% [0.5, 5.9] (2/120)  
Other: 1.7% [0.5, 5.9] (2/120)

## Health checks

- labels: {'correct': 82, 'made_up': 137, 'refused': 103, 'wrong_refusal': 34, 'other': 2, 'wrong': 2}
- three-way outcome (plan): {'correct': 185, 'made_up': 139, 'other': 36}
- answer part taken from: {'first_sentence': 359, 'conclusion': 1}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
