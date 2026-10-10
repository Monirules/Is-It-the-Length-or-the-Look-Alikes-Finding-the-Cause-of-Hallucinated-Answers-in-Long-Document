# Official scoring: gemma3_27b (bfloat16), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 5.8% [3.5, 9.6] (14/240) |
| strong | 92.5% [88.5, 95.2] (222/240) |
| decoy | 5.8% [3.5, 9.6] (14/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 5.8% [3.5, 9.6] (14/240), strong 92.9% [89.0, 95.5] (223/240), decoy 5.8% [3.5, 9.6] (14/240)

## Where the made-up answers came from

Copied the look-alike record's value: 58.8% [52.6, 64.7] (147/250)

| source | count |
|---|---|
| lookalike | 147 |
| other_record | 92 |
| not_in_document | 11 |

## Questions with an answer

Correct: 76.9% [72.3, 81.0] (277/360)  
Wrongly refused: 3.3% [1.9, 5.7] (12/360)  
Wrong value: 19.4% [15.7, 23.8] (70/360)  
Other: 0.3% [0.0, 1.6] (1/360)

## Health checks

- labels: {'refused': 469, 'correct': 277, 'wrong': 70, 'other': 2, 'made_up': 250, 'wrong_refusal': 12}
- three-way outcome (plan): {'correct': 746, 'made_up': 320, 'other': 14}
- answer part taken from: {'first_sentence': 1059, 'conclusion': 21}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
