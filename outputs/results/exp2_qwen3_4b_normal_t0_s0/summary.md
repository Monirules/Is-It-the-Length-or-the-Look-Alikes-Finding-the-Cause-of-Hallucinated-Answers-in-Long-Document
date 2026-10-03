# Official scoring: qwen3_4b (fp8 (PC)), exp2, normal prompt, T=0, 20 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 19.4] (0/16) | 0.0% [0.0, 13.8] (0/24) | 0.0% [0.0, 8.8] (0/40) |
| weak | 0.0% [0.0, 13.8] (0/24) | 0.0% [0.0, 19.4] (0/16) | 0.0% [0.0, 8.8] (0/40) |
| medium | 25.0% [10.2, 49.5] (4/16) | 0.0% [0.0, 13.8] (0/24) | 10.0% [4.0, 23.1] (4/40) |
| strong | 70.8% [50.8, 85.1] (17/24) | 43.8% [23.1, 66.8] (7/16) | 60.0% [44.6, 73.7] (24/40) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 8.8] (0/40), weak 0.0% [0.0, 8.8] (0/40), medium 15.0% [7.1, 29.1] (6/40), strong 75.0% [59.8, 85.8] (30/40)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [87.9, 100.0] (28/28)

| source | count |
|---|---|
| lookalike | 28 |

## Questions with an answer

Correct: 83.8% [74.2, 90.3] (67/80)  
Wrongly refused: 16.2% [9.7, 25.8] (13/80)  
Wrong value: 0.0% [0.0, 4.6] (0/80)  
Other: 0.0% [0.0, 4.6] (0/80)

## Health checks

- labels: {'refused': 132, 'correct': 67, 'wrong_refusal': 13, 'made_up': 28}
- three-way outcome (plan): {'correct': 199, 'other': 13, 'made_up': 28}
- answer part taken from: {'conclusion': 119, 'first_sentence': 111, 'final_line': 10}
- refused first, then gave a value anyway: 5
- truncated at max_tokens: 0
- empty responses: 0
