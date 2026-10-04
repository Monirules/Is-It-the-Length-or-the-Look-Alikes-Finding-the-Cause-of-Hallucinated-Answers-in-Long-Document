# Official scoring: llama33_70b (fp8), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 92.8% [89.4, 95.2] (297/320) | 93.1% [89.8, 95.4] (298/320) | 93.0% [90.7, 94.7] (595/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 93.3% [91.1, 95.0] (597/640)

## Where the made-up answers came from

Copied the look-alike record's value: 93.3% [91.0, 95.0] (555/595)

| source | count |
|---|---|
| lookalike | 555 |
| other_record | 40 |

## Questions with an answer

Correct: 97.5% [95.1, 98.7] (312/320)  
Wrongly refused: 1.9% [0.9, 4.0] (6/320)  
Wrong value: 0.3% [0.1, 1.7] (1/320)  
Other: 0.3% [0.1, 1.7] (1/320)

## Health checks

- labels: {'correct': 312, 'made_up': 595, 'refused': 27, 'other': 19, 'wrong_refusal': 6, 'wrong': 1}
- three-way outcome (plan): {'correct': 339, 'made_up': 596, 'other': 25}
- answer part taken from: {'first_sentence': 959, 'conclusion': 1}
- refused first, then gave a value anyway: 9
- truncated at max_tokens: 4
- empty responses: 0
