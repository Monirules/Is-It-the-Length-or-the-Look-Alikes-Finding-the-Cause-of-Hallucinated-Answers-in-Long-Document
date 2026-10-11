# Official scoring: qwen3_next_80b (fp8), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.0% [0.0, 1.6] (0/240) |
| strong | 89.6% [85.1, 92.8] (215/240) |
| decoy | 0.0% [0.0, 1.6] (0/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), strong 92.5% [88.5, 95.2] (222/240), decoy 0.0% [0.0, 1.6] (0/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.6% [96.0, 99.5] (212/215)

| source | count |
|---|---|
| lookalike | 212 |
| other_record | 3 |

## Questions with an answer

Correct: 98.6% [96.8, 99.4] (355/360)  
Wrongly refused: 0.6% [0.2, 2.0] (2/360)  
Wrong value: 0.8% [0.3, 2.4] (3/360)  
Other: 0.0% [0.0, 1.1] (0/360)

## Health checks

- labels: {'refused': 505, 'correct': 355, 'made_up': 215, 'wrong_refusal': 2, 'wrong': 3}
- three-way outcome (plan): {'correct': 860, 'made_up': 218, 'other': 2}
- answer part taken from: {'first_sentence': 1064, 'final_line': 6, 'conclusion': 10}
- refused first, then gave a value anyway: 8
- truncated at max_tokens: 0
- empty responses: 0
