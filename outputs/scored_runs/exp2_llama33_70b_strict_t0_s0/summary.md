# Official scoring: llama33_70b (fp8), exp2, strict prompt, T=0, 30 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

360 answers from 30 documents: 240 with no answer, 120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 85.8% [78.5, 91.0] (103/120) | 49.2% [40.4, 58.0] (59/120) | 67.5% [61.3, 73.1] (162/240) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 67.5% [61.3, 73.1] (162/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.1% [94.7, 99.4] (159/162)

| source | count |
|---|---|
| lookalike | 159 |
| other_record | 3 |

## Questions with an answer

Correct: 85.8% [78.5, 91.0] (103/120)  
Wrongly refused: 11.7% [7.1, 18.6] (14/120)  
Wrong value: 2.5% [0.9, 7.1] (3/120)  
Other: 0.0% [0.0, 3.1] (0/120)

## Health checks

- labels: {'correct': 103, 'made_up': 162, 'refused': 78, 'wrong': 3, 'wrong_refusal': 14}
- three-way outcome (plan): {'correct': 181, 'made_up': 165, 'other': 14}
- answer part taken from: {'first_sentence': 359, 'final_line': 1}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
