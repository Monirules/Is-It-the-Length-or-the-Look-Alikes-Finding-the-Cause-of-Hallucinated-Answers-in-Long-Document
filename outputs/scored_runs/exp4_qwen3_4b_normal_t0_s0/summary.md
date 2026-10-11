# Official scoring: qwen3_4b (bfloat16), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 89.7% [85.9, 92.6] (287/320) | 62.5% [57.1, 67.6] (200/320) | 76.1% [72.6, 79.2] (487/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 91.1% [88.6, 93.1] (583/640)

## Where the made-up answers came from

Copied the look-alike record's value: 95.3% [93.0, 96.8] (464/487)

| source | count |
|---|---|
| lookalike | 464 |
| other_record | 19 |
| not_in_document | 4 |

## Questions with an answer

Correct: 88.8% [84.8, 91.8] (284/320)  
Wrongly refused: 10.6% [7.7, 14.5] (34/320)  
Wrong value: 0.3% [0.1, 1.7] (1/320)  
Other: 0.3% [0.1, 1.7] (1/320)

## Health checks

- labels: {'correct': 284, 'made_up': 487, 'refused': 153, 'wrong_refusal': 34, 'wrong': 1, 'other': 1}
- three-way outcome (plan): {'correct': 437, 'made_up': 488, 'other': 35}
- answer part taken from: {'first_sentence': 724, 'conclusion': 149, 'final_line': 87}
- refused first, then gave a value anyway: 14
- truncated at max_tokens: 9
- empty responses: 0
