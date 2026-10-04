# Official scoring: qwen3_next_80b (fp8), exp3, normal prompt, T=0, 320 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3840 answers from 320 documents: 2560 with no answer, 1280 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 0.6] (0/640) | 0.0% [0.0, 0.6] (0/640) | 0.0% [0.0, 0.3] (0/1280) |
| strong | 91.9% [89.5, 93.8] (588/640) | 71.2% [67.6, 74.6] (456/640) | 81.6% [79.3, 83.6] (1044/1280) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 0.3] (0/1280), strong 85.4% [83.3, 87.2] (1093/1280)

## Where the made-up answers came from

Copied the look-alike record's value: 99.0% [98.2, 99.5] (1034/1044)

| source | count |
|---|---|
| lookalike | 1034 |
| other_record | 9 |
| not_in_document | 1 |

## Questions with an answer

Correct: 95.5% [94.2, 96.5] (1222/1280)  
Wrongly refused: 3.9% [3.0, 5.1] (50/1280)  
Wrong value: 0.4% [0.2, 0.9] (5/1280)  
Other: 0.2% [0.1, 0.7] (3/1280)

## Health checks

- labels: {'correct': 1222, 'refused': 1508, 'made_up': 1044, 'wrong_refusal': 50, 'other': 11, 'wrong': 5}
- three-way outcome (plan): {'correct': 2730, 'made_up': 1049, 'other': 61}
- answer part taken from: {'first_sentence': 3737, 'final_line': 30, 'conclusion': 73}
- refused first, then gave a value anyway: 40
- truncated at max_tokens: 0
- empty responses: 0
