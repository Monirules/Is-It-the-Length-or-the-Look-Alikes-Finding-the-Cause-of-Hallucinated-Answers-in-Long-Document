# Exp 1 (RQ3): Roig's made-up answers split by look-alike presence

RIKER2 released answers, all temperatures. 418,700 trap answers used; 187,250 failed replies left out; 0 answers to questions we could not read.

35 models; 11 have answers at all three lengths and are used for the averages.

Made-up rate = mean over models of each model's rate; [95% bootstrap interval over models]; (questions).

## All trap questions (L11 + L12)

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 0.0% [0.0, 0.0] (80 q) | 0.0% [0.0, 0.0] (46 q) | +0.0 points |
| 128K | 0.0% [0.0, 0.0] (112 q) | 0.0% [0.0, 0.0] (68 q) | +0.0 points |
| 200K | 0.0% [0.0, 0.0] (142 q) | 0.0% [0.0, 0.0] (91 q) | +0.0 points |

## L12 only (same question type: the record exists, the field does not)

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 0.0% [0.0, 0.0] (17 q) | 0.0% [0.0, 0.0] (46 q) | +0.0 points |
| 128K | 0.0% [0.0, 0.0] (22 q) | 0.0% [0.0, 0.0] (68 q) | +0.0 points |
| 200K | 0.0% [0.0, 0.0] (26 q) | 0.0% [0.0, 0.0] (91 q) | +0.0 points |

## All trap questions, scored with OUR refusal rules

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 0.0% [0.0, 0.0] (80 q) | 0.0% [0.0, 0.0] (46 q) | +0.0 points |
| 128K | 0.0% [0.0, 0.0] (112 q) | 0.0% [0.0, 0.0] (68 q) | +0.0 points |
| 200K | 0.0% [0.0, 0.0] (142 q) | 0.0% [0.0, 0.0] (91 q) | +0.0 points |

## By level and kind of the closest look-alike (pooled over models and runs)

| length | level | closest look-alike | questions | answers | made up (pooled, Wilson 95%) |
|---|---|---|---|---|---|
| 32K | L11 | other_party | 48 | 62,281 | 0.0% [0.0, 0.0] |
| 32K | L11 | shared_name | 15 | 20,581 | 0.0% [0.0, 0.0] |
| 32K | L12 | none | 46 | 60,959 | 0.0% [0.0, 0.0] |
| 32K | L12 | other_date | 16 | 16,004 | 0.0% [0.0, 0.0] |
| 32K | L12 | other_party | 1 | 968 | 0.0% [0.0, 0.4] |
| 128K | L11 | other_party | 70 | 74,371 | 0.0% [0.0, 0.0] |
| 128K | L11 | shared_name | 20 | 22,081 | 0.0% [0.0, 0.0] |
| 128K | L12 | none | 68 | 57,806 | 0.0% [0.0, 0.0] |
| 128K | L12 | other_date | 22 | 19,484 | 0.0% [0.0, 0.0] |
| 200K | L11 | other_party | 91 | 38,639 | 0.0% [0.0, 0.0] |
| 200K | L11 | shared_name | 25 | 11,428 | 0.0% [0.0, 0.0] |
| 200K | L12 | none | 91 | 25,052 | 0.0% [0.0, 0.0] |
| 200K | L12 | other_date | 24 | 8,441 | 0.0% [0.0, 0.0] |
| 200K | L12 | other_party | 2 | 605 | 0.0% [0.0, 0.6] |

## Do look-alikes grow with length? (the confound Exp 1 is about)

| length | trap questions | with a look-alike | mean look-alike records per question |
|---|---|---|---|
| 32K | 126 | 80 (63%) | 0.79 |
| 128K | 180 | 112 (62%) | 0.78 |
| 200K | 233 | 142 (61%) | 0.76 |

## Did made-up answers copy the look-alike's value? (look-alike capture)

| length | question kind | made-up answers with a look-alike value | copied it |
|---|---|---|---|

For yes/no questions half of all answers match by chance, so only the value questions show capture clearly.

## Regression (binomial GLM; each model and question level has its own baseline)

| term | log-odds | 95% CI | odds ratio | p |
|---|---|---|---|---|
| one doubling of length | 0.000 | [-36059.351, 36059.351] | 1.00 | 1 |
| look-alike present | 0.000 | [-124744.520, 124744.520] | 1.00 | 1 |

**Exchange rate (preview):** one look-alike record has the same effect as **0.4 doublings** of length (log-odds ratio 0.000 / 0.000). In RIKER2 look-alikes are not placed on purpose, so this is only a first estimate; Exp 3 measures it properly.

## Check: do we read the data the way Roig did?

Compared 465 (hardware, temperature, model, length) cells with Roig's `<length>k_summary.csv`.
Mean absolute difference in fabrication %: **0.00 points** counting failed replies as wrong; 29.62 points leaving them out. Share of cells within 1 point: 100%.
