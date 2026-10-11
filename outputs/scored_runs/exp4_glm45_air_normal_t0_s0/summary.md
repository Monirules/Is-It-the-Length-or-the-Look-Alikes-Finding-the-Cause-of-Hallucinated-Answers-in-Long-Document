# Official scoring: glm45_air (fp8), exp4, normal prompt, T=0, 80 documents at 32K. Official scoring.

Scoring rules: score/refusal_rules.py, score/match_answer.py, score/capture_tag.py (score-v1).

960 answers from 80 documents: 640 with no answer, 320 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| strong | 99.4% [97.8, 99.8] (318/320) | 96.2% [93.6, 97.8] (308/320) | 97.8% [96.4, 98.7] (626/640) |

Strict reading (made up, or refused but quoted the look-alike's value): strong 97.8% [96.4, 98.7] (626/640)

## Where the made-up answers came from

Copied the look-alike record's value: 97.6% [96.1, 98.5] (611/626)

| source | count |
|---|---|
| lookalike | 611 |
| other_record | 13 |
| not_in_document | 2 |

## Questions with an answer

Correct: 99.7% [98.3, 99.9] (319/320)  
Wrongly refused: 0.0% [0.0, 1.2] (0/320)  
Wrong value: 0.3% [0.1, 1.7] (1/320)  
Other: 0.0% [0.0, 1.2] (0/320)

## Health checks

- labels: {'correct': 319, 'made_up': 626, 'refused': 12, 'other': 2, 'wrong': 1}
- three-way outcome (plan): {'correct': 331, 'made_up': 627, 'other': 2}
- answer part taken from: {'first_sentence': 960}
- refused first, then gave a value anyway: 0
- truncated at max_tokens: 0
- empty responses: 0
