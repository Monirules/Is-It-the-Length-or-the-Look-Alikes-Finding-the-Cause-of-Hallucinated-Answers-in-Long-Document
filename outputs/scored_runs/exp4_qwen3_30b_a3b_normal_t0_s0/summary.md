# Official scoring: qwen3_30b_a3b (bfloat16), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 96.2% [93.6, 97.8] (308/320) | 73.1% [68.0, 77.7] (234/320) | 84.7% [81.7, 87.3] (542/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 84.8% [81.9, 87.4] (543/640)

## Where the made-up answers came from

Copied the look-alike record's value: 98.2% [96.6, 99.0] (532/542)

| source | count |
|---|---|
| lookalike | 532 |
| other_record | 10 |

## Questions with an answer

Correct: 99.1% [97.3, 99.7] (317/320)  
Wrongly refused: 0.9% [0.3, 2.7] (3/320)  
Wrong value: 0.0% [0.0, 1.2] (0/320)  
Other: 0.0% [0.0, 1.2] (0/320)

## Health checks

- labels: {'correct': 317, 'made_up': 542, 'refused': 97, 'other': 1, 'wrong_refusal': 3}
- three-way outcome (plan): {'correct': 414, 'made_up': 542, 'other': 4}
- answer part taken from: {'first_sentence': 948, 'conclusion': 12}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
