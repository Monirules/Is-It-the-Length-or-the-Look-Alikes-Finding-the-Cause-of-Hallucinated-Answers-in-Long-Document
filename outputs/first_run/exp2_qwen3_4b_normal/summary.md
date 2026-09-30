# First look: qwen3_4b (fp8 (PC)), exp2, normal prompt, T=0, 20 documents at 32K. Provisional scoring.

PROVISIONAL scoring (see scripts/first_look.py); official scoring is Jayden's score/.

240 answers from 20 documents: 160 with no answer, 80 with an answer.

## Questions with no answer: made-up answer rate (95% Wilson interval)

| level | name ladder | role ladder | both |
|---|---|---|---|
| none | 0.0% [0.0, 19.4] (0/16) | 0.0% [0.0, 13.8] (0/24) | 0.0% [0.0, 8.8] (0/40) |
| weak | 0.0% [0.0, 13.8] (0/24) | 12.5% [3.5, 36.0] (2/16) | 5.0% [1.4, 16.5] (2/40) |
| medium | 37.5% [18.5, 61.4] (6/16) | 0.0% [0.0, 13.8] (0/24) | 15.0% [7.1, 29.1] (6/40) |
| strong | 75.0% [55.1, 88.0] (18/24) | 75.0% [50.5, 89.8] (12/16) | 75.0% [59.8, 85.8] (30/40) |

## Where the made-up answers came from

Made-up answers that copied the look-alike record's value: 94.7% [82.7, 98.5] (36/38)

| level | made up | copied look-alike |
|---|---|---|
| none | 0 | 0 |
| weak | 2 | 0 |
| medium | 6 | 6 |
| strong | 30 | 30 |

## Questions with an answer

Correct: 85.0% [75.6, 91.2] (68/80)  
Wrongly refused: 15.0% [8.8, 24.4] (12/80)  
Wrong value: 0.0% [0.0, 4.6] (0/80)

## Health checks

- labels: {'refused': 121, 'other': 1, 'correct': 68, 'wrong_refusal': 12, 'made_up': 38}
- truncated at max_tokens: 0
- empty responses: 0
- document reuse: questions 2-12 took 38,787 of 38,820 prompt tokens from the cache on average
