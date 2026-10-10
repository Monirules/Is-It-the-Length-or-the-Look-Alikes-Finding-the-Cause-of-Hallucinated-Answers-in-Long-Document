# Official scoring: llama33_70b_bf16 (bfloat16), exp3, normal prompt, T=0, 80 documents at 128K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 56.2% [48.5, 63.7] (90/160) | 80.0% [73.1, 85.5] (128/160) | 68.1% [62.8, 73.0] (218/320) |
| strong | 76.9% [69.8, 82.7] (123/160) | 93.8% [88.9, 96.6] (150/160) | 85.3% [81.0, 88.8] (273/320) |

Strict reading (made up, or refused but quoted the look-alike's value): none 68.1% [62.8, 73.0] (218/320), strong 85.6% [81.4, 89.0] (274/320)

## Where the made-up answers came from

Copied the look-alike record's value: 33.2% [29.2, 37.5] (163/491)

| source | count |
|---|---|
| other_record | 298 |
| lookalike | 163 |
| not_in_document | 30 |

## Questions with an answer

Correct: 48.4% [43.0, 53.9] (155/320)  
Wrongly refused: 10.0% [7.2, 13.8] (32/320)  
Wrong value: 40.9% [35.7, 46.4] (131/320)  
Other: 0.6% [0.2, 2.2] (2/320)

## Health checks

- labels: {'made_up': 491, 'correct': 155, 'refused': 148, 'wrong': 131, 'wrong_refusal': 32, 'other': 3}
- three-way outcome (plan): {'made_up': 622, 'correct': 303, 'other': 35}
- answer part taken from: {'first_sentence': 959, 'conclusion': 1}
- refused first, then gave a value anyway: 12
- truncated at max_tokens: 0
- empty responses: 0
