# Official scoring: gemma3_27b (bfloat16), exp2, normal prompt, T=0, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 5.0% [2.3, 10.5] (6/120) | 5.0% [2.3, 10.5] (6/120) | 5.0% [2.9, 8.5] (12/240) |
| weak | 20.0% [13.8, 28.0] (24/120) | 24.2% [17.4, 32.6] (29/120) | 22.1% [17.3, 27.7] (53/240) |
| medium | 99.2% [95.4, 99.9] (119/120) | 43.3% [34.8, 52.3] (52/120) | 71.2% [65.2, 76.6] (171/240) |
| strong | 99.2% [95.4, 99.9] (119/120) | 82.5% [74.7, 88.3] (99/120) | 90.8% [86.5, 93.9] (218/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 5.0% [2.9, 8.5] (12/240), weak 30.4% [24.9, 36.5] (73/240), medium 81.2% [75.8, 85.7] (195/240), strong 94.2% [90.4, 96.5] (226/240)

## Where the made-up answers came from

Copied the look-alike record's value: 57.9% [53.3, 62.4] (263/454)

| source | count |
|---|---|
| lookalike | 263 |
| other_record | 170 |
| not_in_document | 21 |

## Questions with an answer

Correct: 79.8% [76.0, 83.1] (383/480)  
Wrongly refused: 3.3% [2.1, 5.3] (16/480)  
Wrong value: 16.9% [13.8, 20.5] (81/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'wrong': 81, 'refused': 505, 'correct': 383, 'made_up': 454, 'wrong_refusal': 16, 'other': 1}
- three-way outcome (plan): {'made_up': 535, 'correct': 888, 'other': 17}
- answer part taken from: {'first_sentence': 1412, 'conclusion': 28}
- refused first, then gave a value anyway: 1
- truncated at max_tokens: 0
- empty responses: 0
