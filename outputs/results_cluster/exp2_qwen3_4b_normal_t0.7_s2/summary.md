# Official scoring: qwen3_4b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 28.3% [21.0, 37.0] (34/120) | 1.7% [0.5, 5.9] (2/120) | 15.0% [11.0, 20.1] (36/240) |
| strong | 79.2% [71.1, 85.5] (95/120) | 44.2% [35.6, 53.1] (53/120) | 61.7% [55.4, 67.6] (148/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.0% [0.0, 1.6] (0/240), medium 24.6% [19.6, 30.4] (59/240), strong 76.2% [70.5, 81.2] (183/240)

## Where the made-up answers came from

Copied the look-alike record's value: 100.0% [98.0, 100.0] (184/184)

| source | count |
|---|---|
| lookalike | 184 |

## Questions with an answer

Correct: 94.4% [91.9, 96.1] (453/480)  
Wrongly refused: 5.2% [3.6, 7.6] (25/480)  
Wrong value: 0.2% [0.0, 1.2] (1/480)  
Other: 0.2% [0.0, 1.2] (1/480)

## Health checks

- labels: {'correct': 453, 'refused': 772, 'made_up': 184, 'wrong_refusal': 25, 'other': 5, 'wrong': 1}
- three-way outcome (plan): {'correct': 1225, 'made_up': 185, 'other': 30}
- answer part taken from: {'first_sentence': 651, 'conclusion': 721, 'final_line': 68}
- refused first, then gave a value anyway: 27
- truncated at max_tokens: 0
- empty responses: 0
