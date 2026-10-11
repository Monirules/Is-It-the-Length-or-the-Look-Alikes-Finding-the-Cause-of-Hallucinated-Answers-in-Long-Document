# Official scoring: llama31_8b (bfloat16), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 48.0% [42.4, 53.6] (144/300) | 55.7% [50.0, 61.2] (167/300) |
| random | 0.0% [0.0, 1.3] (0/300) | 0.3% [0.1, 1.9] (1/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 51.8% [47.8, 55.8] (311/600), random 0.2% [0.0, 0.9] (1/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 1.2] (0/312)

| source | count |
|---|---|
| not_the_true_answer | 275 |
| true_answer_from_memory | 37 |

## Questions with an answer

Correct: 39.7% [34.3, 45.3] (119/300)  
Wrongly refused: 31.7% [26.7, 37.1] (95/300)  
Wrong value: 28.7% [23.8, 34.0] (86/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong_refusal': 95, 'refused': 888, 'made_up': 312, 'correct': 119, 'wrong': 86}
- three-way outcome (plan): {'other': 95, 'correct': 1007, 'made_up': 398}
- answer part taken from: {'first_sentence': 1500}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 9
- empty responses: 0
