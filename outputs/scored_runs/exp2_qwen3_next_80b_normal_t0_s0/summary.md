# Official scoring: qwen3_next_80b (fp8), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 41.7% [33.2, 50.6] (50/120) | 7.5% [4.0, 13.6] (9/120) | 24.6% [19.6, 30.4] (59/240) |
| strong | 95.0% [89.5, 97.7] (114/120) | 78.3% [70.1, 84.8] (94/120) | 86.7% [81.8, 90.4] (208/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 34.2% [28.5, 40.4] (82/240), strong 90.0% [85.6, 93.2] (216/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.1% [95.7, 99.2] (262/267)

| source | count |
|---|---|
| lookalike | 262 |
| other_record | 5 |

## Questions with an answer

Correct: 99.0% [97.6, 99.6] (475/480)  
Wrongly refused: 0.8% [0.3, 2.1] (4/480)  
Wrong value: 0.2% [0.0, 1.2] (1/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 475, 'refused': 690, 'made_up': 267, 'wrong_refusal': 4, 'other': 3, 'wrong': 1}
- three-way outcome (plan): {'correct': 1165, 'made_up': 268, 'other': 7}
- answer part taken from: {'first_sentence': 1378, 'final_line': 20, 'conclusion': 42}
- refused first, then gave a value anyway: 39
- truncated at max_tokens: 0
- empty responses: 0
