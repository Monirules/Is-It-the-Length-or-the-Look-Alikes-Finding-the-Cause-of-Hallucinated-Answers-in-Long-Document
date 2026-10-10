# Official scoring: llama33_70b (fp8), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.4% [0.1, 2.3] (1/240) |
| strong | 91.7% [87.5, 94.5] (220/240) |
| decoy | 0.0% [0.0, 1.6] (0/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), strong 92.9% [89.0, 95.5] (223/240), decoy 0.0% [0.0, 1.6] (0/240)

## Where the made-up answers came from

Copied the look-alike record's value: 93.2% [89.1, 95.8] (206/221)

| source | count |
|---|---|
| lookalike | 206 |
| other_record | 15 |

## Questions with an answer

Correct: 98.1% [96.0, 99.1] (353/360)  
Wrongly refused: 0.8% [0.3, 2.4] (3/360)  
Wrong value: 0.6% [0.2, 2.0] (2/360)  
Other: 0.6% [0.2, 2.0] (2/360)

## Health checks

- labels: {'refused': 499, 'correct': 353, 'wrong': 2, 'made_up': 221, 'other': 2, 'wrong_refusal': 3}
- three-way outcome (plan): {'correct': 852, 'made_up': 223, 'other': 5}
- answer part taken from: {'first_sentence': 1080}
- refused first, then gave a value anyway: 3
- truncated at max_tokens: 0
- empty responses: 0
