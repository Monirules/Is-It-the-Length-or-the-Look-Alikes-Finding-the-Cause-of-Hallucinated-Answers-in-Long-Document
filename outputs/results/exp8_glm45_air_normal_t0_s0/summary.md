# Official scoring: glm45_air (fp8), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.4% [0.1, 2.3] (1/240) |
| strong | 95.0% [91.5, 97.1] (228/240) |
| decoy | 0.4% [0.1, 2.3] (1/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), strong 95.0% [91.5, 97.1] (228/240), decoy 0.4% [0.1, 2.3] (1/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.7% [96.2, 99.6] (227/230)

| source | count |
|---|---|
| lookalike | 227 |
| other_record | 3 |

## Questions with an answer

Correct: 99.7% [98.4, 100.0] (359/360)  
Wrongly refused: 0.0% [0.0, 1.1] (0/360)  
Wrong value: 0.3% [0.0, 1.6] (1/360)  
Other: 0.0% [0.0, 1.1] (0/360)

## Health checks

- labels: {'refused': 490, 'correct': 359, 'made_up': 230, 'wrong': 1}
- three-way outcome (plan): {'correct': 849, 'made_up': 231}
- answer part taken from: {'first_sentence': 1080}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
