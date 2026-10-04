# Official scoring: glm45_air (fp8), exp3, normal prompt, T=0, 280 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3360 answers from 280 documents: 2240 with no answer, 1120 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 0.7] (0/560) | 6.1% [4.4, 8.4] (34/560) | 3.0% [2.2, 4.2] (34/1120) |
| strong | 85.5% [82.4, 88.2] (479/560) | 88.9% [86.1, 91.3] (498/560) | 87.2% [85.1, 89.1] (977/1120) |

Strict reading (made up, or refused but quoted the look-alike's value): none 3.0% [2.2, 4.2] (34/1120), strong 87.2% [85.1, 89.1] (977/1120)

## Where the made-up answers came from

Copied the look-alike record's value: 94.8% [93.2, 96.0] (958/1011)

| source | count |
|---|---|
| lookalike | 958 |
| other_record | 50 |
| not_in_document | 3 |

## Questions with an answer

Correct: 96.2% [95.0, 97.2] (1078/1120)  
Wrongly refused: 1.6% [1.0, 2.5] (18/1120)  
Wrong value: 2.1% [1.4, 3.1] (23/1120)  
Other: 0.1% [0.0, 0.5] (1/1120)

## Health checks

- labels: {'correct': 1078, 'refused': 1224, 'made_up': 1011, 'other': 6, 'wrong_refusal': 18, 'wrong': 23}
- three-way outcome (plan): {'correct': 2302, 'made_up': 1034, 'other': 24}
- answer part taken from: {'first_sentence': 3360}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
