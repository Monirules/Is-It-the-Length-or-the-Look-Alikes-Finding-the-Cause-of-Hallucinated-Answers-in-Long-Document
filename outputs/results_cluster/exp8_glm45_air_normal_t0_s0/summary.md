# Official scoring: glm45_air (fp8), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

2160 answers from 90 documents: 1440 with no answer, 720 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.6% [0.2, 1.8] (3/480) |
| strong | 94.8% [92.4, 96.4] (455/480) |
| decoy | 0.4% [0.1, 1.5] (2/480) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.6% [0.2, 1.8] (3/480), strong 94.8% [92.4, 96.4] (455/480), decoy 0.4% [0.1, 1.5] (2/480)

## Where the made-up answers came from

Copied the look-alike record's value: 98.5% [96.9, 99.3] (453/460)

| source | count |
|---|---|
| lookalike | 453 |
| other_record | 7 |

## Questions with an answer

Correct: 99.7% [99.0, 99.9] (718/720)  
Wrongly refused: 0.0% [0.0, 0.5] (0/720)  
Wrong value: 0.3% [0.1, 1.0] (2/720)  
Other: 0.0% [0.0, 0.5] (0/720)

## Health checks

- labels: {'refused': 979, 'correct': 718, 'made_up': 460, 'wrong': 2, 'other': 1}
- three-way outcome (plan): {'correct': 1697, 'made_up': 462, 'other': 1}
- answer part taken from: {'first_sentence': 2160}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
