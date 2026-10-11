# Official scoring: qwen3_30b_a3b (bfloat16), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 97.5% [92.9, 99.1] (117/120) | 66.7% [57.8, 74.5] (80/120) | 82.1% [76.7, 86.4] (197/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 83.8% [78.6, 87.9] (201/240)

## Where the made-up answers came from

Copied the look-alike record's value: 96.4% [92.8, 98.3] (190/197)

| source | count |
|---|---|
| lookalike | 190 |
| other_record | 7 |

## Questions with an answer

Correct: 96.7% [91.7, 98.7] (116/120)  
Wrongly refused: 0.0% [0.0, 3.1] (0/120)  
Wrong value: 3.3% [1.3, 8.3] (4/120)  
Other: 0.0% [0.0, 3.1] (0/120)

## Health checks

- labels: {'correct': 116, 'made_up': 197, 'wrong': 4, 'refused': 43}
- three-way outcome (plan): {'correct': 159, 'made_up': 201}
- answer part taken from: {'first_sentence': 335, 'final_line': 13, 'conclusion': 12}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 0
- empty responses: 0
