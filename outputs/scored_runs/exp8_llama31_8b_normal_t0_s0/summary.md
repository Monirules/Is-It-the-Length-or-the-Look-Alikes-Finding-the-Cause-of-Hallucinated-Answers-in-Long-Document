# Official scoring: llama31_8b (bfloat16), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.0% [0.0, 1.6] (0/240) |
| strong | 58.3% [52.0, 64.4] (140/240) |
| decoy | 0.0% [0.0, 1.6] (0/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), strong 58.3% [52.0, 64.4] (140/240), decoy 0.0% [0.0, 1.6] (0/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.6% [94.9, 99.6] (138/140)

| source | count |
|---|---|
| lookalike | 138 |
| other_record | 2 |

## Questions with an answer

Correct: 84.7% [80.6, 88.1] (305/360)  
Wrongly refused: 14.4% [11.2, 18.5] (52/360)  
Wrong value: 0.8% [0.3, 2.4] (3/360)  
Other: 0.0% [0.0, 1.1] (0/360)

## Health checks

- labels: {'refused': 580, 'correct': 305, 'made_up': 140, 'wrong_refusal': 52, 'wrong': 3}
- three-way outcome (plan): {'correct': 885, 'made_up': 143, 'other': 52}
- answer part taken from: {'first_sentence': 1080}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
