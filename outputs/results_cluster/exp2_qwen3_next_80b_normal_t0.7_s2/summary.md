# Official scoring: qwen3_next_80b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 41.7% [33.2, 50.6] (50/120) | 6.7% [3.4, 12.6] (8/120) | 24.2% [19.2, 30.0] (58/240) |
| strong | 95.0% [89.5, 97.7] (114/120) | 72.5% [63.9, 79.7] (87/120) | 83.8% [78.6, 87.9] (201/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 35.8% [30.0, 42.1] (86/240), strong 87.5% [82.7, 91.1] (210/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.5% [96.1, 99.4] (255/259)

| source | count |
|---|---|
| lookalike | 255 |
| other_record | 4 |

## Questions with an answer

Correct: 99.2% [97.9, 99.7] (476/480)  
Wrongly refused: 0.6% [0.2, 1.8] (3/480)  
Wrong value: 0.2% [0.0, 1.2] (1/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 476, 'refused': 696, 'made_up': 259, 'other': 5, 'wrong': 1, 'wrong_refusal': 3}
- three-way outcome (plan): {'correct': 1172, 'made_up': 260, 'other': 8}
- answer part taken from: {'first_sentence': 1375, 'conclusion': 48, 'final_line': 17}
- refused first, then gave a value anyway: 34
- truncated at max_tokens: 0
- empty responses: 0
