# Official scoring: llama31_8b (bfloat16), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 3.3% [1.3, 8.3] (4/120) | 0.8% [0.1, 4.6] (1/120) | 2.1% [0.9, 4.8] (5/240) |
| weak | 5.8% [2.9, 11.6] (7/120) | 13.3% [8.4, 20.6] (16/120) | 9.6% [6.5, 14.0] (23/240) |
| medium | 38.3% [30.1, 47.3] (46/120) | 8.3% [4.6, 14.7] (10/120) | 23.3% [18.4, 29.1] (56/240) |
| strong | 88.3% [81.4, 92.9] (106/120) | 41.7% [33.2, 50.6] (50/120) | 65.0% [58.8, 70.8] (156/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 2.1% [0.9, 4.8] (5/240), weak 12.5% [8.9, 17.3] (30/240), medium 32.9% [27.3, 39.1] (79/240), strong 67.5% [61.3, 73.1] (162/240)

## Where the made-up answers came from

Copied the look-alike record's value: 91.7% [87.5, 94.5] (220/240)

| source | count |
|---|---|
| lookalike | 220 |
| other_record | 18 |
| not_in_document | 2 |

## Questions with an answer

Correct: 80.4% [76.6, 83.7] (386/480)  
Wrongly refused: 17.9% [14.7, 21.6] (86/480)  
Wrong value: 1.0% [0.4, 2.4] (5/480)  
Other: 0.6% [0.2, 1.8] (3/480)

## Health checks

- labels: {'correct': 386, 'refused': 716, 'made_up': 240, 'other': 7, 'wrong': 5, 'wrong_refusal': 86}
- three-way outcome (plan): {'correct': 1102, 'made_up': 245, 'other': 93}
- answer part taken from: {'first_sentence': 1439, 'conclusion': 1}
- refused first, then gave a value anyway: 2
- truncated at max_tokens: 1
- empty responses: 0
