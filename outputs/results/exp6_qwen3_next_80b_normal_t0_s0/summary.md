# Official scoring: qwen3_next_80b (fp8), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 78.0% [73.0, 82.3] (234/300) | 87.0% [82.7, 90.3] (261/300) |
| random | 1.0% [0.3, 2.9] (3/300) | 2.0% [0.9, 4.3] (6/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 82.5% [79.3, 85.3] (495/600), random 1.5% [0.8, 2.8] (9/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 0.8] (0/504)

| source | count |
|---|---|
| not_the_true_answer | 366 |
| true_answer_from_memory | 138 |

## Questions with an answer

Correct: 59.7% [54.0, 65.1] (179/300)  
Wrongly refused: 4.7% [2.8, 7.7] (14/300)  
Wrong value: 35.7% [30.5, 41.2] (107/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong': 107, 'refused': 696, 'made_up': 504, 'correct': 179, 'wrong_refusal': 14}
- three-way outcome (plan): {'made_up': 611, 'correct': 875, 'other': 14}
- answer part taken from: {'first_sentence': 1452, 'final_line': 17, 'conclusion': 31}
- refused first, then gave a value anyway: 5
- truncated at max_tokens: 5
- empty responses: 0
