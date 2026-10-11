# Official scoring: qwen3_4b (bfloat16), exp3, normal prompt, T=0, 320 documents at 128K/32K/64K/8K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

3840 answers from 320 documents: 2560 with no answer, 1280 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 0.6] (0/640) | 2.0% [1.2, 3.4] (13/640) | 1.0% [0.6, 1.7] (13/1280) |
| strong | 70.2% [66.5, 73.6] (449/640) | 57.7% [53.8, 61.4] (369/640) | 63.9% [61.2, 66.5] (818/1280) |

Strict reading (made up, or refused but quoted the look-alike's value): none 1.0% [0.6, 1.7] (13/1280), strong 72.1% [69.6, 74.5] (923/1280)

## Where the made-up answers came from

Copied the look-alike record's value: 91.3% [89.2, 93.1] (759/831)

| source | count |
|---|---|
| lookalike | 759 |
| other_record | 61 |
| not_in_document | 11 |

## Questions with an answer

Correct: 82.7% [80.6, 84.7] (1059/1280)  
Wrongly refused: 12.5% [10.8, 14.4] (160/1280)  
Wrong value: 4.1% [3.1, 5.3] (52/1280)  
Other: 0.7% [0.4, 1.3] (9/1280)

## Health checks

- labels: {'correct': 1059, 'refused': 1712, 'made_up': 831, 'wrong_refusal': 160, 'other': 26, 'wrong': 52}
- three-way outcome (plan): {'correct': 2771, 'made_up': 883, 'other': 186}
- answer part taken from: {'first_sentence': 2291, 'conclusion': 1414, 'final_line': 135}
- refused first, then gave a value anyway: 12
- truncated at max_tokens: 0
- empty responses: 0
