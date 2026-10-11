# Official scoring: qwen3_next_80b (fp8), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 97.8% [95.6, 98.9] (313/320) | 77.8% [72.9, 82.0] (249/320) | 87.8% [85.0, 90.1] (562/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 93.4% [91.2, 95.1] (598/640)

## Where the made-up answers came from

Copied the look-alike record's value: 97.2% [95.4, 98.2] (546/562)

| source | count |
|---|---|
| lookalike | 546 |
| other_record | 16 |

## Questions with an answer

Correct: 98.4% [96.4, 99.3] (315/320)  
Wrongly refused: 1.6% [0.7, 3.6] (5/320)  
Wrong value: 0.0% [0.0, 1.2] (0/320)  
Other: 0.0% [0.0, 1.2] (0/320)

## Health checks

- labels: {'correct': 315, 'made_up': 562, 'refused': 77, 'wrong_refusal': 5, 'other': 1}
- three-way outcome (plan): {'correct': 392, 'made_up': 562, 'other': 6}
- answer part taken from: {'first_sentence': 922, 'final_line': 12, 'conclusion': 26}
- refused first, then gave a value anyway: 4
- truncated at max_tokens: 3
- empty responses: 0
