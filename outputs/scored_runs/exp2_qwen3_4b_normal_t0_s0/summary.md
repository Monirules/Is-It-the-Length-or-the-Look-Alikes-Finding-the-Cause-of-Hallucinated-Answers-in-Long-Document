# Official scoring: qwen3_4b (bfloat16), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.8% [0.1, 4.6] (1/120) | 0.0% [0.0, 3.1] (0/120) | 0.4% [0.1, 2.3] (1/240) |
| medium | 30.8% [23.3, 39.6] (37/120) | 0.8% [0.1, 4.6] (1/120) | 15.8% [11.8, 21.0] (38/240) |
| strong | 80.8% [72.9, 86.9] (97/120) | 49.2% [40.4, 58.0] (59/120) | 65.0% [58.8, 70.8] (156/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.4% [0.1, 2.3] (1/240), medium 28.3% [23.0, 34.3] (68/240), strong 76.2% [70.5, 81.2] (183/240)

## Where the made-up answers came from

Copied the look-alike record's value: 99.5% [97.2, 99.9] (194/195)

| source | count |
|---|---|
| lookalike | 194 |
| not_in_document | 1 |

## Questions with an answer

Correct: 94.6% [92.2, 96.3] (454/480)  
Wrongly refused: 5.0% [3.4, 7.3] (24/480)  
Wrong value: 0.0% [0.0, 0.8] (0/480)  
Other: 0.4% [0.1, 1.5] (2/480)

## Health checks

- labels: {'correct': 454, 'refused': 762, 'wrong_refusal': 24, 'made_up': 195, 'other': 5}
- three-way outcome (plan): {'correct': 1216, 'other': 29, 'made_up': 195}
- answer part taken from: {'first_sentence': 661, 'conclusion': 714, 'final_line': 65}
- refused first, then gave a value anyway: 29
- truncated at max_tokens: 0
- empty responses: 0
