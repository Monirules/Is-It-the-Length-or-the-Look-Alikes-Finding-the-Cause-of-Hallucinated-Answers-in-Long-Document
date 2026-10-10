# Official scoring: gemma3_27b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 5.0% [2.3, 10.5] (6/120) | 6.7% [3.4, 12.6] (8/120) | 5.8% [3.5, 9.6] (14/240) |
| weak | 23.3% [16.7, 31.7] (28/120) | 24.2% [17.4, 32.6] (29/120) | 23.8% [18.8, 29.5] (57/240) |
| medium | 100.0% [96.9, 100.0] (120/120) | 43.3% [34.8, 52.3] (52/120) | 71.7% [65.7, 77.0] (172/240) |
| strong | 99.2% [95.4, 99.9] (119/120) | 80.8% [72.9, 86.9] (97/120) | 90.0% [85.6, 93.2] (216/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 5.8% [3.5, 9.6] (14/240), weak 34.2% [28.5, 40.4] (82/240), medium 84.6% [79.5, 88.6] (203/240), strong 93.3% [89.4, 95.9] (224/240)

## Where the made-up answers came from

Copied the look-alike record's value: 57.5% [53.0, 62.0] (264/459)

| source | count |
|---|---|
| lookalike | 264 |
| other_record | 175 |
| not_in_document | 20 |

## Questions with an answer

Correct: 79.4% [75.5, 82.8] (381/480)  
Wrongly refused: 3.1% [1.9, 5.1] (15/480)  
Wrong value: 17.5% [14.4, 21.2] (84/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'wrong': 84, 'refused': 500, 'correct': 381, 'made_up': 459, 'wrong_refusal': 15, 'other': 1}
- three-way outcome (plan): {'made_up': 543, 'correct': 881, 'other': 16}
- answer part taken from: {'first_sentence': 1409, 'conclusion': 31}
- refused first, then gave a value anyway: 3
- truncated at max_tokens: 0
- empty responses: 0
