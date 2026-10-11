# Official scoring: qwen3_4b (bfloat16), exp6, normal prompt, T=0, 1500 documents at 32K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1500 answers from 1500 documents: 1200 with no answer, 300 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 8K | 32K |
|---|---|---|
| lookalike | 57.3% [51.7, 62.8] (172/300) | 65.3% [59.8, 70.5] (196/300) |
| random | 0.0% [0.0, 1.3] (0/300) | 0.3% [0.1, 1.9] (1/300) |

Strict reading (made up, or refused but quoted the look-alike's value): lookalike 61.3% [57.4, 65.1] (368/600), random 0.2% [0.0, 0.9] (1/600)

## Where the made-up answers came from

Copied the look-alike record's value: 0.0% [0.0, 1.0] (0/369)

| source | count |
|---|---|
| not_the_true_answer | 341 |
| true_answer_from_memory | 28 |

## Questions with an answer

Correct: 47.3% [41.8, 53.0] (142/300)  
Wrongly refused: 16.0% [12.3, 20.6] (48/300)  
Wrong value: 36.7% [31.4, 42.3] (110/300)  
Other: 0.0% [0.0, 1.3] (0/300)

## Health checks

- labels: {'wrong_refusal': 48, 'refused': 831, 'made_up': 369, 'correct': 142, 'wrong': 110}
- three-way outcome (plan): {'other': 48, 'correct': 973, 'made_up': 479}
- answer part taken from: {'first_sentence': 1120, 'conclusion': 329, 'final_line': 51}
- refused first, then gave a value anyway: 42
- truncated at max_tokens: 27
- empty responses: 0
