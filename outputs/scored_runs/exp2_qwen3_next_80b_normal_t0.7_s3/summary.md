# Official scoring: qwen3_next_80b (fp8), exp2, normal prompt, T=0.7, 120 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1440 answers from 120 documents: 960 with no answer, 480 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| weak | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 3.1] (0/120) | 0.0% [0.0, 1.6] (0/240) |
| medium | 35.0% [27.1, 43.9] (42/120) | 8.3% [4.6, 14.7] (10/120) | 21.7% [16.9, 27.3] (52/240) |
| strong | 93.3% [87.4, 96.6] (112/120) | 74.2% [65.7, 81.2] (89/120) | 83.8% [78.6, 87.9] (201/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), weak 0.0% [0.0, 1.6] (0/240), medium 31.2% [25.7, 37.4] (75/240), strong 87.9% [83.2, 91.5] (211/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.8% [96.6, 99.6] (250/253)

| source | count |
|---|---|
| lookalike | 250 |
| other_record | 3 |

## Questions with an answer

Correct: 99.2% [97.9, 99.7] (476/480)  
Wrongly refused: 0.6% [0.2, 1.8] (3/480)  
Wrong value: 0.2% [0.0, 1.2] (1/480)  
Other: 0.0% [0.0, 0.8] (0/480)

## Health checks

- labels: {'correct': 476, 'refused': 705, 'made_up': 253, 'wrong': 1, 'other': 2, 'wrong_refusal': 3}
- three-way outcome (plan): {'correct': 1181, 'made_up': 254, 'other': 5}
- answer part taken from: {'first_sentence': 1380, 'conclusion': 45, 'final_line': 15}
- refused first, then gave a value anyway: 32
- truncated at max_tokens: 0
- empty responses: 0
