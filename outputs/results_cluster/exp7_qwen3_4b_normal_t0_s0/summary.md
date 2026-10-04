# Official scoring: qwen3_4b (bfloat16), exp7, normal prompt, T=0, 20 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 77.5% [67.2, 85.3] (62/80) | 48.8% [38.1, 59.5] (39/80) | 63.1% [55.4, 70.2] (101/160) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 76.2% [69.1, 82.2] (122/160)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [96.3, 100.0] (101/101)

| source | count |
|---|---|
| lookalike | 101 |

## Questions with an answer

Correct: 92.5% [84.6, 96.5] (74/80)  
Wrongly refused: 7.5% [3.5, 15.4] (6/80)  
Wrong value: 0.0% [0.0, 4.6] (0/80)  
Other: 0.0% [0.0, 4.6] (0/80)

## Health checks

- labels: {'made_up': 101, 'correct': 74, 'refused': 59, 'wrong_refusal': 6}
- three-way outcome (plan): {'made_up': 101, 'correct': 133, 'other': 6}
- answer part taken from: {'first_sentence': 161, 'conclusion': 59, 'final_line': 20}
- refused first, then gave a value anyway: 4
- truncated at max_tokens: 0
- empty responses: 0
