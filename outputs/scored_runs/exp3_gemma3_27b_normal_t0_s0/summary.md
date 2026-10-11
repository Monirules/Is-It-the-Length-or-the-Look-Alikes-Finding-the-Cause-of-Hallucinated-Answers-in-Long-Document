# Official scoring: gemma3_27b (bfloat16), exp3, normal prompt, T=0, 240 documents at 32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

2880 answers from 240 documents: 1920 with no answer, 960 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 2.9% [1.7, 4.8] (14/480) | 15.6% [12.7, 19.1] (75/480) | 9.3% [7.6, 11.3] (89/960) |
| strong | 97.3% [95.4, 98.4] (467/480) | 86.7% [83.3, 89.4] (416/480) | 92.0% [90.1, 93.5] (883/960) |

Strict reading (made up, or refused but quoted the look-alike's value): none 9.3% [7.6, 11.3] (89/960), strong 93.2% [91.5, 94.7] (895/960)

## Where the made-up answers came from

Copied the look-alike record's value: 60.7% [57.6, 63.7] (590/972)

| source | count |
|---|---|
| lookalike | 590 |
| other_record | 343 |
| not_in_document | 39 |

## Questions with an answer

Correct: 73.8% [70.9, 76.4] (708/960)  
Wrongly refused: 3.8% [2.7, 5.1] (36/960)  
Wrong value: 22.5% [20.0, 25.2] (216/960)  
Other: 0.0% [0.0, 0.4] (0/960)

## Health checks

- labels: {'correct': 708, 'refused': 947, 'made_up': 972, 'wrong_refusal': 36, 'wrong': 216, 'other': 1}
- three-way outcome (plan): {'correct': 1655, 'made_up': 1188, 'other': 37}
- answer part taken from: {'first_sentence': 2806, 'conclusion': 74}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
