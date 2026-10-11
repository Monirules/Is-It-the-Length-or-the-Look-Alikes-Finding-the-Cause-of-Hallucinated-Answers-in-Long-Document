# Official scoring: gemma3_27b (bfloat16), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 97.8% [95.6, 98.9] (313/320) | 97.5% [95.1, 98.7] (312/320) | 97.7% [96.2, 98.6] (625/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 98.1% [96.8, 98.9] (628/640)

## Where the made-up answers came from

Copied the look-alike record's value: 82.9% [79.7, 85.6] (518/625)

| source | count |
|---|---|
| lookalike | 518 |
| other_record | 93 |
| not_in_document | 14 |

## Questions with an answer

Correct: 80.0% [75.3, 84.0] (256/320)  
Wrongly refused: 5.0% [3.1, 8.0] (16/320)  
Wrong value: 15.0% [11.5, 19.3] (48/320)  
Other: 0.0% [0.0, 1.2] (0/320)

## Health checks

- labels: {'correct': 256, 'made_up': 625, 'wrong': 48, 'other': 6, 'wrong_refusal': 16, 'refused': 9}
- three-way outcome (plan): {'correct': 265, 'made_up': 673, 'other': 22}
- answer part taken from: {'first_sentence': 957, 'conclusion': 3}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 1
- empty responses: 0
