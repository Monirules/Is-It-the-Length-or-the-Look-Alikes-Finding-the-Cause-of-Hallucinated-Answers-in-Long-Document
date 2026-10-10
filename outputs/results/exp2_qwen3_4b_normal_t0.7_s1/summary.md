# Official scoring: qwen3_4b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 26.7% [19.6, 35.2] (32/120) | 1.7% [0.5, 5.9] (2/120) | 14.2% [10.3, 19.1] (34/240) |
| strong | 80.8% [72.9, 86.9] (97/120) | 47.5% [38.8, 56.4] (57/120) | 64.2% [57.9, 70.0] (154/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 26.7% [21.5, 32.6] (64/240), strong 78.3% [72.7, 83.1] (188/240)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [98.0, 100.0] (188/188)

| source | count |
|---|---|
| lookalike | 188 |

## Questions with an answer

Correct: 94.6% [92.2, 96.3] (454/480)  
Wrongly refused: 5.0% [3.4, 7.3] (24/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.4% [0.1, 1.5] (2/480)

## Health checks

- labels: {'correct': 454, 'refused': 769, 'wrong_refusal': 24, 'made_up': 188, 'other': 5}
- three-way outcome (plan): {'correct': 1223, 'other': 29, 'made_up': 188}
- answer part taken from: {'first_sentence': 658, 'conclusion': 720, 'final_line': 62}
- refused first, then gave a value anyway: 27
- truncated at max_tokens: 0
- empty responses: 0
