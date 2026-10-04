# Official scoring: llama31_8b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.8% [0.1, 4.6] (1/120) | 0.4% [0.1, 2.3] (1/240) |
| weak | 3.3% [1.3, 8.3] (4/120) | 7.5% [4.0, 13.6] (9/120) | 5.4% [3.2, 9.0] (13/240) |
| medium | 32.5% [24.8, 41.3] (39/120) | 7.5% [4.0, 13.6] (9/120) | 20.0% [15.4, 25.5] (48/240) |
| strong | 87.5% [80.4, 92.3] (105/120) | 44.2% [35.6, 53.1] (53/120) | 65.8% [59.6, 71.5] (158/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.4% [0.1, 2.3] (1/240), weak 8.3% [5.5, 12.5] (20/240), medium 29.6% [24.2, 35.6] (71/240), strong 67.1% [60.9, 72.7] (161/240)

## Where the made-up answers came from

Copied the look-alike record's value: 95.0% [91.3, 97.2] (209/220)

| source | count |
|---|---|
| lookalike | 209 |
| other_record | 10 |
| not_in_document | 1 |

## Questions with an answer

Correct: 81.5% [77.7, 84.7] (391/480)  
Wrongly refused: 17.7% [14.6, 21.4] (85/480)  
Wrong value: 0.8% [0.3, 2.1] (4/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'wrong_refusal': 85, 'refused': 740, 'correct': 391, 'made_up': 220, 'wrong': 4}
- three-way outcome (plan): {'other': 85, 'correct': 1131, 'made_up': 224}
- answer part taken from: {'first_sentence': 1439, 'conclusion': 1}
- refused first, then gave a value anyway: 2
- truncated at max_tokens: 0
- empty responses: 0
