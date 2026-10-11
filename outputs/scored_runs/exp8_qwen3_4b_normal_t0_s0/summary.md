# Official scoring: qwen3_4b (bfloat16), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.0% [0.0, 1.6] (0/240) |
| strong | 63.7% [57.5, 69.6] (153/240) |
| decoy | 0.0% [0.0, 1.6] (0/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), strong 78.8% [73.1, 83.5] (189/240), decoy 0.0% [0.0, 1.6] (0/240)

## Where the made-up answers came from

Copied the look-alike record's value: 99.3% [96.4, 99.9] (152/153)

| source | count |
|---|---|
| lookalike | 152 |
| other_record | 1 |

## Questions with an answer

Correct: 95.6% [92.9, 97.2] (344/360)  
Wrongly refused: 4.2% [2.5, 6.8] (15/360)  
Wrong value: 0.3% [0.0, 1.6] (1/360)  
Other: 0.0% [0.0, 1.1] (0/360)

## Health checks

- labels: {'refused': 567, 'correct': 344, 'wrong_refusal': 15, 'made_up': 153, 'wrong': 1}
- three-way outcome (plan): {'correct': 911, 'other': 15, 'made_up': 154}
- answer part taken from: {'conclusion': 537, 'first_sentence': 508, 'final_line': 35}
- refused first, then gave a value anyway: 5
- truncated at max_tokens: 0
- empty responses: 0
