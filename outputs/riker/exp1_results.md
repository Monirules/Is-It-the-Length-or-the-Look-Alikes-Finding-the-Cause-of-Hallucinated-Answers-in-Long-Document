# Exp 1 (RQ3): Roig's made-up answers split by look-alike presence

RIKER2 released answers, all temperatures. 605,948 trap answers used; 2 failed replies left out; 0 answers to questions we could not read.

35 models; 11 have answers at all three lengths and are used for the averages.

Made-up rate = mean over models of each model's rate; [95% bootstrap interval over models]; (questions).

## All trap questions (L11 + L12)

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 29.4% [21.5, 37.2] (80 q) | 19.1% [11.6, 27.6] (46 q) | +10.2 points |
| 128K | 22.2% [14.8, 30.0] (112 q) | 40.2% [29.6, 50.2] (68 q) | -18.0 points |
| 200K | 33.0% [22.6, 44.0] (142 q) | 53.7% [44.2, 62.2] (91 q) | -20.8 points |

## L12 only (same question type: the record exists, the field does not)

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 42.5% [26.8, 57.5] (17 q) | 19.1% [11.6, 27.6] (46 q) | +23.4 points |
| 128K | 37.5% [25.5, 50.0] (22 q) | 40.2% [29.6, 50.2] (68 q) | -2.7 points |
| 200K | 45.4% [32.7, 57.7] (26 q) | 53.7% [44.2, 62.2] (91 q) | -8.3 points |

## All trap questions, scored with OUR refusal rules

| length | look-alike present | no look-alike | difference |
|---|---|---|---|
| 32K | 29.3% [21.4, 37.1] (80 q) | 18.6% [11.2, 26.8] (46 q) | +10.6 points |
| 128K | 22.0% [14.6, 29.7] (112 q) | 39.4% [28.7, 49.6] (68 q) | -17.5 points |
| 200K | 32.8% [22.5, 43.5] (142 q) | 52.9% [43.3, 61.3] (91 q) | -20.1 points |

## By level and kind of the closest look-alike (pooled over models and runs)

| length | level | closest look-alike | questions | answers | made up (pooled, Wilson 95%) |
|---|---|---|---|---|---|
| 32K | L11 | other_party | 48 | 82,512 | 24.5% [24.2, 24.8] |
| 32K | L11 | shared_name | 15 | 25,785 | 20.2% [19.7, 20.7] |
| 32K | L12 | none | 46 | 79,074 | 22.9% [22.6, 23.2] |
| 32K | L12 | other_date | 16 | 27,504 | 41.8% [41.2, 42.4] |
| 32K | L12 | other_party | 1 | 1,719 | 43.7% [41.4, 46.0] |
| 128K | L11 | other_party | 70 | 94,150 | 21.0% [20.7, 21.3] |
| 128K | L11 | shared_name | 20 | 26,900 | 17.9% [17.5, 18.4] |
| 128K | L12 | none | 68 | 91,460 | 36.8% [36.5, 37.1] |
| 128K | L12 | other_date | 22 | 29,590 | 34.2% [33.6, 34.7] |
| 200K | L11 | other_party | 91 | 57,511 | 32.8% [32.4, 33.2] |
| 200K | L11 | shared_name | 25 | 15,799 | 27.7% [27.0, 28.4] |
| 200K | L12 | none | 91 | 57,512 | 56.4% [56.0, 56.8] |
| 200K | L12 | other_date | 24 | 15,168 | 44.3% [43.6, 45.1] |
| 200K | L12 | other_party | 2 | 1,264 | 52.1% [49.4, 54.9] |

## Do look-alikes grow with length? (the confound Exp 1 is about)

| length | trap questions | with a look-alike | mean look-alike records per question |
|---|---|---|---|
| 32K | 126 | 80 (63%) | 0.79 |
| 128K | 180 | 112 (62%) | 0.78 |
| 200K | 233 | 142 (61%) | 0.76 |

## Did made-up answers copy the look-alike's value? (look-alike capture)

| length | question kind | made-up answers with a look-alike value | copied it |
|---|---|---|---|
| 32K | value (amount, date, name, ...) | 20,757 | 50.3% |
| 32K | yes/no | 16,929 | 81.8% |
| 128K | value (amount, date, name, ...) | 18,079 | 50.2% |
| 128K | yes/no | 16,625 | 65.0% |
| 200K | value (amount, date, name, ...) | 15,872 | 53.4% |
| 200K | yes/no | 14,757 | 67.2% |

For yes/no questions half of all answers match by chance, so only the value questions show capture clearly.

## Regression (binomial GLM; each model and question level has its own baseline)

| term | log-odds | 95% CI | odds ratio | p |
|---|---|---|---|---|
| one doubling of length | 0.284 | [0.277, 0.290] | 1.33 | 0 |
| look-alike present | 0.157 | [0.139, 0.176] | 1.17 | 1.4e-63 |

**Exchange rate (preview):** one look-alike record has the same effect as **0.6 doublings** of length (log-odds ratio 0.157 / 0.284). In RIKER2 look-alikes are not placed on purpose, so this is only a first estimate; Exp 3 measures it properly.

## Check: do we read the data the way Roig did?

Compared 465 (hardware, temperature, model, length) cells with Roig's `<length>k_summary.csv`.
Mean absolute difference in fabrication %: **0.00 points** counting failed replies as wrong; 0.00 points leaving them out. Share of cells within 1 point: 100%.
