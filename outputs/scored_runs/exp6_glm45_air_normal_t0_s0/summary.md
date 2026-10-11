# Official scoring: glm45_air (fp8), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 58.3% [52.7, 63.8] (175/300) | 61.3% [55.7, 66.7] (184/300) |
| random | 1.7% [0.7, 3.8] (5/300) | 5.3% [3.3, 8.5] (16/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 59.8% [55.9, 63.7] (359/600), random 3.5% [2.3, 5.3] (21/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 1.0] (0/380)

| source | count |
|---|---|
| not_the_true_answer | 323 |
| true_answer_from_memory | 57 |

## Questions with an answer

Correct: 48.3% [42.7, 54.0] (145/300)  
Wrongly refused: 18.3% [14.4, 23.1] (55/300)  
Wrong value: 33.3% [28.2, 38.8] (100/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong': 100, 'made_up': 380, 'refused': 820, 'correct': 145, 'wrong_refusal': 55}
- three-way outcome (plan): {'made_up': 480, 'correct': 965, 'other': 55}
- answer part taken from: {'first_sentence': 1500}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 16
- empty responses: 0
