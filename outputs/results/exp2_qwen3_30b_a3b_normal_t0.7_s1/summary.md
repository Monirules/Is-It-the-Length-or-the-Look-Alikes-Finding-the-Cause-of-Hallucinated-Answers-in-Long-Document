# Official scoring: qwen3_30b_a3b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 1.7% [0.5, 5.9] (2/120) | 4.2% [1.8, 9.4] (5/120) | 2.9% [1.4, 5.9] (7/240) |
| weak | 0.8% [0.1, 4.6] (1/120) | 15.8% [10.4, 23.4] (19/120) | 8.3% [5.5, 12.5] (20/240) |
| medium | 30.8% [23.3, 39.6] (37/120) | 30.0% [22.5, 38.7] (36/120) | 30.4% [24.9, 36.5] (73/240) |
| strong | 97.5% [92.9, 99.1] (117/120) | 70.0% [61.3, 77.5] (84/120) | 83.8% [78.6, 87.9] (201/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 2.9% [1.4, 5.9] (7/240), weak 8.3% [5.5, 12.5] (20/240), medium 31.2% [25.7, 37.4] (75/240), strong 84.6% [79.5, 88.6] (203/240)

## Where the made-up answers came from

Copied the look-alike record's value: 94.4% [91.1, 96.4] (284/301)

| source | count |
|---|---|
| lookalike | 284 |
| other_record | 13 |
| not_in_document | 4 |

## Questions with an answer

Correct: 99.8% [98.8, 100.0] (479/480)  
Wrongly refused: 0.2% [0.0, 1.2] (1/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 479, 'refused': 653, 'made_up': 301, 'other': 6, 'wrong_refusal': 1}
- three-way outcome (plan): {'correct': 1132, 'made_up': 301, 'other': 7}
- answer part taken from: {'first_sentence': 1297, 'conclusion': 143}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
