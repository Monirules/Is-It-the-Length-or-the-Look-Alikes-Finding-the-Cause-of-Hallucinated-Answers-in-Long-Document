# Official scoring: qwen3_30b_a3b (bfloat16), exp8, normal prompt, T=0, 90 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

1080 answers from 90 documents: 720 with no answer, 360 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| filler | 32K |
|---|---|
| none | 0.0% [0.0, 1.6] (0/240) |
| strong | 80.4% [74.9, 84.9] (193/240) |
| decoy | 0.8% [0.2, 3.0] (2/240) |

Strict reading (made up, or refused but quoted the look-alike's value): none 0.0% [0.0, 1.6] (0/240), strong 80.8% [75.4, 85.3] (194/240), decoy 0.8% [0.2, 3.0] (2/240)

## Where the made-up answers came from

Copied the look-alike record's value: 98.5% [95.6, 99.5] (192/195)

| source | count |
|---|---|
| lookalike | 192 |
| other_record | 2 |
| not_in_document | 1 |

## Questions with an answer

Correct: 100.0% [98.9, 100.0] (360/360)  
Wrongly refused: 0.0% [0.0, 1.1] (0/360)  
Wrong value: 0.0% [0.0, 1.1] (0/360)  
Other: 0.0% [0.0, 1.1] (0/360)

## Health checks

- labels: {'refused': 522, 'correct': 360, 'made_up': 195, 'other': 3}
- three-way outcome (plan): {'correct': 882, 'made_up': 195, 'other': 3}
- answer part taken from: {'first_sentence': 978, 'conclusion': 102}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
