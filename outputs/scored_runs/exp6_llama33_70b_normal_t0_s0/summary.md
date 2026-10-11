# Official scoring: llama33_70b (fp8), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 65.7% [60.1, 70.8] (197/300) | 77.0% [71.9, 81.4] (231/300) |
| random | 2.0% [0.9, 4.3] (6/300) | 12.7% [9.4, 16.9] (38/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 71.3% [67.6, 74.8] (428/600), random 7.3% [5.5, 9.7] (44/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 0.8] (0/472)

| source | count |
|---|---|
| not_the_true_answer | 341 |
| true_answer_from_memory | 131 |

## Questions with an answer

Correct: 63.7% [58.1, 68.9] (191/300)  
Wrongly refused: 5.3% [3.3, 8.5] (16/300)  
Wrong value: 31.0% [26.0, 36.4] (93/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong_refusal': 16, 'refused': 728, 'made_up': 472, 'correct': 191, 'wrong': 93}
- three-way outcome (plan): {'other': 16, 'correct': 919, 'made_up': 565}
- answer part taken from: {'first_sentence': 1500}
- refused first, then gave a value anyway: 3
- truncated at max_tokens: 0
- empty responses: 0
