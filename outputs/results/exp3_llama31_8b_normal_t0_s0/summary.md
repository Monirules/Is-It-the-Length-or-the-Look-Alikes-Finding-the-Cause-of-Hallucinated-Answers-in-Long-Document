# Official scoring: llama31_8b (bfloat16), exp3, normal prompt, T=0, 320 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3840 answers from 320 documents: 2560 with no answer, 1280 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 2.0% [1.2, 3.4] (13/640) | 1.1% [0.5, 2.2] (7/640) | 1.6% [1.0, 2.4] (20/1280) |
| strong | 83.6% [80.5, 86.3] (535/640) | 39.4% [35.7, 43.2] (252/640) | 61.5% [58.8, 64.1] (787/1280) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.6% [1.0, 2.4] (20/1280), strong 63.3% [60.6, 65.9] (810/1280)

## Where the made-up answers came from

Copied the look-alike record's value: 93.2% [91.2, 94.7] (752/807)

| source | count |
|---|---|
| lookalike | 752 |
| other_record | 45 |
| not_in_document | 10 |

## Questions with an answer

Correct: 70.9% [68.4, 73.4] (908/1280)  
Wrongly refused: 25.2% [22.9, 27.6] (322/1280)  
Wrong value: 3.5% [2.6, 4.7] (45/1280)  
Other: 0.4% [0.2, 0.9] (5/1280)

## Health checks

- labels: {'correct': 908, 'refused': 1747, 'wrong_refusal': 322, 'other': 11, 'made_up': 807, 'wrong': 45}
- three-way outcome (plan): {'correct': 2655, 'other': 333, 'made_up': 852}
- answer part taken from: {'first_sentence': 3840}
- refused first, then gave a value anyway: 3
- truncated at max_tokens: 0
- empty responses: 0
