# Official scoring: gemma3_27b (bfloat16), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 82.0% [77.3, 85.9] (246/300) | 84.7% [80.2, 88.3] (254/300) |
| random | 4.0% [2.3, 6.9] (12/300) | 1.0% [0.3, 2.9] (3/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 83.3% [80.1, 86.1] (500/600), random 2.5% [1.5, 4.1] (15/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 0.7] (0/515)

| source | count |
|---|---|
| not_the_true_answer | 461 |
| true_answer_from_memory | 54 |

## Questions with an answer

Correct: 55.3% [49.7, 60.9] (166/300)  
Wrongly refused: 3.0% [1.6, 5.6] (9/300)  
Wrong value: 41.7% [36.2, 47.3] (125/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong': 125, 'refused': 685, 'made_up': 515, 'correct': 166, 'wrong_refusal': 9}
- three-way outcome (plan): {'made_up': 640, 'correct': 851, 'other': 9}
- answer part taken from: {'first_sentence': 1478, 'conclusion': 22}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 6
- empty responses: 0
