# Official scoring: qwen3_30b_a3b (bfloat16), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 77.3% [72.3, 81.7] (232/300) | 80.7% [75.8, 84.7] (242/300) |
| random | 0.0% [0.0, 1.3] (0/300) | 1.0% [0.3, 2.9] (3/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 79.0% [75.6, 82.1] (474/600), random 0.5% [0.2, 1.5] (3/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 0.8] (0/477)

| source | count |
|---|---|
| not_the_true_answer | 383 |
| true_answer_from_memory | 94 |

## Questions with an answer

Correct: 54.7% [49.0, 60.2] (164/300)  
Wrongly refused: 6.3% [4.1, 9.7] (19/300)  
Wrong value: 39.0% [33.7, 44.6] (117/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong': 117, 'refused': 723, 'made_up': 477, 'correct': 164, 'wrong_refusal': 19}
- three-way outcome (plan): {'made_up': 594, 'correct': 887, 'other': 19}
- answer part taken from: {'conclusion': 30, 'first_sentence': 1469, 'final_line': 1}
- refused first, then gave a value anyway: 3
- truncated at max_tokens: 3
- empty responses: 0
