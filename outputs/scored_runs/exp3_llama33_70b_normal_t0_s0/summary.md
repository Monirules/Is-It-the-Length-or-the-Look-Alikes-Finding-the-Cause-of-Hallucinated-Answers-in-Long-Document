# Official scoring: llama33_70b (fp8), exp3, normal prompt, T=0, 320 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3840 answers from 320 documents: 2560 with no answer, 1280 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 15.8% [13.2, 18.8] (101/640) | 21.9% [18.8, 25.2] (140/640) | 18.8% [16.8, 21.1] (241/1280) |
| strong | 91.6% [89.2, 93.5] (586/640) | 85.5% [82.5, 88.0] (547/640) | 88.5% [86.7, 90.1] (1133/1280) |

Strict reading (made up, or refused but quoted the look-alike's value): none 18.8% [16.8, 21.1] (241/1280), strong 90.0% [88.2, 91.5] (1152/1280)

## Where the made-up answers came from

Copied the look-alike record's value: 72.7% [70.3, 75.0] (999/1374)

| source | count |
|---|---|
| lookalike | 999 |
| other_record | 352 |
| not_in_document | 23 |

## Questions with an answer

Correct: 81.0% [78.8, 83.1] (1037/1280)  
Wrongly refused: 6.1% [4.9, 7.5] (78/1280)  
Wrong value: 12.3% [10.6, 14.2] (157/1280)  
Other: 0.6% [0.3, 1.2] (8/1280)

## Health checks

- labels: {'correct': 1037, 'refused': 1176, 'made_up': 1374, 'wrong_refusal': 78, 'wrong': 157, 'other': 18}
- three-way outcome (plan): {'correct': 2213, 'made_up': 1531, 'other': 96}
- answer part taken from: {'first_sentence': 3837, 'conclusion': 3}
- refused first, then gave a value anyway: 22
- truncated at max_tokens: 2
- empty responses: 0
