# Official scoring: llama31_8b (bfloat16), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 73.4% [68.3, 78.0] (235/320) | 41.6% [36.3, 47.0] (133/320) | 57.5% [53.6, 61.3] (368/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 59.1% [55.2, 62.8] (378/640)

## Where the made-up answers came from

Copied the look-alike record's value: 97.0% [94.7, 98.3] (357/368)

| source | count |
|---|---|
| lookalike | 357 |
| other_record | 10 |
| not_in_document | 1 |

## Questions with an answer

Correct: 77.2% [72.3, 81.4] (247/320)  
Wrongly refused: 21.9% [17.7, 26.7] (70/320)  
Wrong value: 0.9% [0.3, 2.7] (3/320)  
Other: 0.0% [0.0, 1.2] (0/320)

## Health checks

- labels: {'correct': 247, 'made_up': 368, 'refused': 270, 'wrong_refusal': 70, 'wrong': 3, 'other': 2}
- three-way outcome (plan): {'correct': 517, 'made_up': 371, 'other': 72}
- answer part taken from: {'first_sentence': 960}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
