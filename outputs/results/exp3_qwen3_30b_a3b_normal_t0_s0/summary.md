# Official scoring: qwen3_30b_a3b (bfloat16), exp3, normal prompt, T=0, 320 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3840 answers from 320 documents: 2560 with no answer, 1280 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.2% [0.0, 0.9] (1/640) | 7.2% [5.4, 9.5] (46/640) | 3.7% [2.8, 4.8] (47/1280) |
| strong | 83.8% [80.7, 86.4] (536/640) | 82.0% [78.9, 84.8] (525/640) | 82.9% [80.7, 84.9] (1061/1280) |

Strict reading (made up, or refused but quoted the look-alike's value): none 3.7% [2.8, 4.8] (47/1280), strong 83.6% [81.5, 85.5] (1070/1280)

## Where the made-up answers came from

Copied the look-alike record's value: 94.9% [93.4, 96.0] (1051/1108)

| source | count |
|---|---|
| lookalike | 1051 |
| other_record | 46 |
| not_in_document | 11 |

## Questions with an answer

Correct: 98.7% [97.9, 99.2] (1263/1280)  
Wrongly refused: 0.7% [0.4, 1.3] (9/1280)  
Wrong value: 0.6% [0.3, 1.2] (8/1280)  
Other: 0.0% [0.0, 0.3] (0/1280)

## Health checks

- labels: {'correct': 1263, 'refused': 1445, 'made_up': 1108, 'other': 7, 'wrong': 8, 'wrong_refusal': 9}
- three-way outcome (plan): {'correct': 2708, 'made_up': 1116, 'other': 16}
- answer part taken from: {'first_sentence': 3504, 'conclusion': 336}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
