# Main results (official scoring)

Models with results: Qwen3 4B, Llama 3.1 8B, Gemma 3 27B, Qwen3 30B-A3B, Llama 3.3 70B, Qwen3-Next 80B, GLM-4.5-Air.

Made-up rate = share of questions with no answer where the model gave a value; 95% Wilson interval in brackets.

## Exp 2: look-alike ladder at 32K (T = 0)

| model | none | weak | medium | strong | copied look-alike | correct (with answer) |
|---|---|---|---|---|---|---|
| Qwen3 4B | 0.0 [0-2] | 0.4 [0-2] | 15.8 [12-21] | 65.0 [59-71] | 99% | 94.6% |
| Llama 3.1 8B | 0.4 [0-2] | 0.8 [0-3] | 14.6 [11-20] | 64.6 [58-70] | 98% | 80.8% |
| Gemma 3 27B | 5.0 [3-9] | 22.1 [17-28] | 71.2 [65-77] | 90.8 [87-94] | 58% | 79.8% |
| Qwen3 30B-A3B | 1.7 [1-4] | 9.6 [6-14] | 25.8 [21-32] | 82.9 [78-87] | 96% | 99.6% |
| Llama 3.3 70B | 0.0 [0-2] | 5.4 [3-9] | 44.2 [38-50] | 94.2 [90-96] | 95% | 98.3% |
| Qwen3-Next 80B | 0.0 [0-2] | 0.0 [0-2] | 24.6 [20-30] | 86.7 [82-90] | 98% | 99.0% |
| GLM-4.5-Air | 0.4 [0-2] | 10.4 [7-15] | 24.2 [19-30] | 93.3 [89-96] | 94% | 100.0% |

## Exp 2 stability: strong look-alike at T = 0.7, three seeds

| model | T=0 | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| Qwen3 4B | 65.0 [59-71] | 64.2 [58-70] | 61.7 [55-68] | 63.7 [57-70] |
| Llama 3.1 8B | 64.6 [58-70] | 69.2 [63-75] | 65.0 [59-71] | 65.8 [60-72] |
| Gemma 3 27B | 90.8 [87-94] | 90.0 [86-93] | 91.2 [87-94] | 90.8 [87-94] |
| Qwen3 30B-A3B | 82.9 [78-87] | 83.8 [79-88] | 82.9 [78-87] | 83.3 [78-88] |
| Llama 3.3 70B | 94.2 [90-96] | 96.2 [93-98] | 95.8 [93-98] | 94.2 [90-96] |
| Qwen3-Next 80B | 86.7 [82-90] | 86.2 [81-90] | 83.8 [79-88] | 83.8 [79-88] |
| GLM-4.5-Air | 93.3 [89-96] | 92.1 [88-95] | 91.2 [87-94] | 90.0 [86-93] |

## Exp 3: length, with and without a strong look-alike (fillers pooled)

| model | none 8K | none 32K | none 64K | none 128K | strong 8K | strong 32K | strong 64K | strong 128K |
|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | 0.0 [0-1] | 0.0 [0-1] | 0.9 [0-3] | 3.1 [2-6] | 69.7 [64-74] | 57.5 [52-63] | 68.4 [63-73] | 60.0 [55-65] |
| Llama 3.1 8B | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 6.2 [4-9] | 62.5 [57-68] | 56.6 [51-62] | 62.8 [57-68] | 64.1 [59-69] |
| Gemma 3 27B | 0.6 [0-2] | 5.9 [4-9] | 21.2 [17-26] | - | 96.2 [94-98] | 92.8 [89-95] | 86.9 [83-90] | - |
| Qwen3 30B-A3B | 0.6 [0-2] | 2.5 [1-5] | 3.4 [2-6] | 8.1 [6-12] | 85.6 [81-89] | 83.8 [79-87] | 79.4 [75-83] | 82.8 [78-87] |
| Llama 3.3 70B | 0.0 [0-1] | 0.3 [0-2] | 0.6 [0-2] | 74.4 [69-79] | 89.7 [86-93] | 89.4 [86-92] | 85.3 [81-89] | 89.7 [86-93] |
| Qwen3-Next 80B | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 86.6 [82-90] | 83.1 [79-87] | 80.3 [76-84] | 76.2 [71-81] |
| GLM-4.5-Air | 0.0 [0-1] | 0.6 [0-2] | 1.2 [0-3] | 17.5 [12-24] | 91.9 [88-94] | 92.8 [89-95] | 87.8 [84-91] | 65.6 [58-73] |

Answer accuracy on questions WITH an answer, Exp 3 (checks that a model can still read at that length):

| model | 8K | 32K | 64K | 128K |
|---|---|---|---|---|
| Qwen3 4B | 95.0% | 87.2% | 83.4% | 65.3% |
| Llama 3.1 8B | 76.9% | 71.9% | 74.7% | 60.3% |
| Gemma 3 27B | 98.1% | 78.1% | 45.0% | - |
| Qwen3 30B-A3B | 100.0% | 99.4% | 98.1% | 97.2% |
| Llama 3.3 70B | 98.4% | 93.4% | 84.4% | 47.8% |
| Qwen3-Next 80B | 99.4% | 96.6% | 95.3% | 90.6% |
| GLM-4.5-Air | 100.0% | 99.1% | 98.1% | 79.4% |

## Exp 3: filler type with a strong look-alike (all lengths)

| model | unrelated filler | sibling filler |
|---|---|---|
| Qwen3 4B | 73.8 [70-77] | 54.1 [50-58] |
| Llama 3.1 8B | 67.7 [64-71] | 55.3 [51-59] |
| Gemma 3 27B | 93.8 [91-96] | 90.2 [87-93] |
| Qwen3 30B-A3B | 83.8 [81-86] | 82.0 [79-85] |
| Llama 3.3 70B | 94.8 [93-96] | 82.2 [79-85] |
| Qwen3-Next 80B | 85.6 [83-88] | 77.5 [74-81] |
| GLM-4.5-Air | 94.0 [91-96] | 82.2 [79-85] |

## Exp 4: copies of the same strong look-alike (32K)

| model | 1 copy | 2 copies | 4 copies | 8 copies |
|---|---|---|---|---|
| Qwen3 4B | 62.5 [55-70] | 76.9 [70-83] | 81.9 [75-87] | 83.1 [77-88] |
| Llama 3.1 8B | 58.8 [51-66] | 67.5 [60-74] | 61.3 [54-68] | 42.5 [35-50] |
| Gemma 3 27B | 96.2 [92-98] | 98.8 [96-100] | 100.0 [98-100] | 95.6 [91-98] |
| Qwen3 30B-A3B | 81.9 [75-87] | 90.0 [84-94] | 85.0 [79-90] | 81.9 [75-87] |
| Llama 3.3 70B | 94.4 [90-97] | 98.1 [95-99] | 95.6 [91-98] | 83.8 [77-89] |
| Qwen3-Next 80B | 86.9 [81-91] | 91.9 [87-95] | 93.8 [89-97] | 78.8 [72-84] |
| GLM-4.5-Air | 95.0 [90-97] | 98.8 [96-100] | 99.4 [97-100] | 98.1 [95-99] |

## Exp 6: real Wikipedia text (Natural Questions, gold passage removed)

Made-up rate on questions whose answer was removed; 300 questions per cell. 'From memory' = made-up answers that are in fact the true answer (the model knew it without the document).

| model | look-alike 8K | random 8K | look-alike 32K | random 32K | from memory | control: correct with gold passage (8K) |
|---|---|---|---|---|---|---|
| Qwen3 4B | 57.3 [52-63] | 0.0 [0-1] | 65.3 [60-70] | 0.3 [0-2] | 8% | 47.3% |
| Llama 3.1 8B | 48.0 [42-54] | 0.0 [0-1] | 55.7 [50-61] | 0.3 [0-2] | 12% | 39.7% |
| Gemma 3 27B | 82.0 [77-86] | 4.0 [2-7] | 84.7 [80-88] | 1.0 [0-3] | 10% | 55.3% |
| Qwen3 30B-A3B | 77.3 [72-82] | 0.0 [0-1] | 80.7 [76-85] | 1.0 [0-3] | 20% | 54.7% |
| Llama 3.3 70B | 65.7 [60-71] | 2.0 [1-4] | 77.0 [72-81] | 12.7 [9-17] | 28% | 63.7% |
| Qwen3-Next 80B | 78.0 [73-82] | 1.0 [0-3] | 87.0 [83-90] | 2.0 [1-4] | 27% | 59.7% |
| GLM-4.5-Air | 58.3 [53-64] | 1.7 [1-4] | 61.3 [56-67] | 5.3 [3-8] | 15% | 48.3% |

## Exp 7: one question per call vs 12 questions in one call (32K, strong look-alike)

| model | made up: one per call | made up: 12 in one call | correct (with answer): one per call | correct: 12 in one call |
|---|---|---|---|---|
| Qwen3 4B | 63.1 [55-70] | 75.6 [68-82] | 92.5% | 78.8% |
| Llama 3.1 8B | 57.5 [50-65] | 95.0 [90-97] | 77.5% | 88.8% |

## Exp 3: breaking length (no look-alike, fillers pooled)

Break = first length whose 95% interval lies fully above the 8K interval. Accuracy drop = first length whose accuracy interval lies fully below the 8K interval and is at least 10 points lower. Documents = documents run at that length (fewer than 80 = only part fit the model's window). Defined on 6 Oct 2026, after seeing the data.

| model | made up, no look-alike: 8K / 32K / 64K / 128K | answer accuracy: 8K / 32K / 64K / 128K | documents | breaking length | made up there | accuracy there | accuracy drop starts |
|---|---|---|---|---|---|---|---|
| Qwen3 4B | 0.0 / 0.0 / 0.9 / 3.1 | 95.0 / 87.2 / 83.4 / 65.3 | 80 / 80 / 80 / 80 | 128K | 3.1 [2-6] | 65.3% | 64K |
| Llama 3.1 8B | 0.0 / 0.0 / 0.0 / 6.2 | 76.9 / 71.9 / 74.7 / 60.3 | 80 / 80 / 80 / 80 | 128K | 6.2 [4-9] | 60.3% | 128K |
| Gemma 3 27B | 0.6 / 5.9 / 21.2 / - | 98.1 / 78.1 / 45.0 / - | 80 / 80 / 80 / 0 | 32K | 5.9 [4-9] | 78.1% | 32K |
| Qwen3 30B-A3B | 0.6 / 2.5 / 3.4 / 8.1 | 100.0 / 99.4 / 98.1 / 97.2 | 80 / 80 / 80 / 80 | 128K | 8.1 [6-12] | 97.2% | none |
| Llama 3.3 70B | 0.0 / 0.3 / 0.6 / 74.4 | 98.4 / 93.4 / 84.4 / 47.8 | 80 / 80 / 80 / 80 | 128K | 74.4 [69-79] | 47.8% | 64K |
| Qwen3-Next 80B | 0.0 / 0.0 / 0.0 / 0.0 | 99.4 / 96.6 / 95.3 / 90.6 | 80 / 80 / 80 / 80 | none up to 128K | - | - | none |
| GLM-4.5-Air | 0.0 / 0.6 / 1.2 / 17.5 | 100.0 / 99.1 / 98.1 / 79.4 | 80 / 80 / 80 / 40 | 128K | 17.5 [12-24] | 79.4% | 128K |

## Exp 3: filler type and answer accuracy (pre-registered prediction 4)

Questions WITH an answer, all lengths: accuracy, wrong refusals (said not found) and wrong values, in %.

| model | made up (strong): unrelated | sibling | accuracy: unrelated | sibling | change (points) | wrong refusals: unrelated / sibling | wrong values: unrelated / sibling |
|---|---|---|---|---|---|---|---|
| Qwen3 4B | 73.8 [70-77] | 54.1 [50-58] | 90.9 | 74.5 | -16.4 | 7.7 / 17.3 | 1.4 / 6.7 |
| Llama 3.1 8B | 67.7 [64-71] | 55.3 [51-59] | 83.0 | 58.9 | -24.1 | 14.8 / 35.5 | 1.9 / 5.2 |
| Gemma 3 27B | 93.8 [91-96] | 90.2 [87-93] | 79.0 | 68.5 | -10.4 | 3.3 / 4.2 | 17.7 / 27.3 |
| Qwen3 30B-A3B | 83.8 [81-86] | 82.0 [79-85] | 99.5 | 97.8 | -1.7 | 0.2 / 1.2 | 0.3 / 0.9 |
| Llama 3.3 70B | 94.8 [93-96] | 82.2 [79-85] | 90.0 | 72.0 | -18.0 | 2.0 / 10.2 | 7.7 / 16.9 |
| Qwen3-Next 80B | 85.6 [83-88] | 77.5 [74-81] | 98.9 | 92.0 | -6.9 | 0.6 / 7.2 | 0.5 / 0.3 |
| GLM-4.5-Air | 94.0 [91-96] | 82.2 [79-85] | 100.0 | 93.4 | -6.6 | 0.0 / 2.8 | 0.0 / 3.6 |

**Prediction 4: partly supported.** Sibling filler lowers made-up answers in 7 of 7 models, but answer accuracy changes by -24.1 to -1.7 points (accuracy does NOT hold).

## Exp 2, strong look-alike: normal prompt vs strict prompt (32K)

| model | made up: normal | strict | accuracy: normal | strict |
|---|---|---|---|---|
| Qwen3 4B | 65.0 [59-71] | 49.6 [43-56] | 95.8 | 90.0 |
| Llama 3.1 8B | 64.6 [58-70] | 57.1 [51-63] | 75.0 | 68.3 |
| Gemma 3 27B | 90.8 [87-94] | 77.9 [72-83] | 82.5 | 70.0 |
| Qwen3 30B-A3B | 82.9 [78-87] | 82.1 [77-86] | 100.0 | 96.7 |
| Llama 3.3 70B | 94.2 [90-96] | 67.5 [61-73] | 97.5 | 85.8 |
| Qwen3-Next 80B | 86.7 [82-90] | 53.8 [47-60] | 100.0 | 95.0 |

## Logistic regression, Exp 3, MAIN RESULT: all Exp 3 answers (16,960 no-answer questions)

made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model

| term | log-odds | SE | odds ratio |
|---|---|---|---|
| one doubling of length | 0.115 | 0.017 | 1.12 |
| strong look-alike | 4.818 | 0.068 | 123.7 |
| sibling filler | -0.537 | 0.050 | 0.58 |

**Exchange rate:** one strong look-alike adds as much as **5.9 doublings of length** (95% document-bootstrap interval 5.5 to 6.3, 500 draws); i.e. a document 58x longer (log-odds 10.69 for the look-alike at 8K / 1.83 per doubling without a look-alike).
With an interaction term: one doubling raises the log-odds by 1.826 (SE 0.092) without a look-alike and by -0.097 with a strong one.

## Logistic regression, Exp 3, SENSITIVITY CHECK (added after seeing the data, not the main result): without Llama 3.3 70B at 128K, where its reading collapses (16,320 no-answer questions)

made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model

| term | log-odds | SE | odds ratio |
|---|---|---|---|
| one doubling of length | -0.008 | 0.018 | 0.99 |
| strong look-alike | 5.468 | 0.085 | 236.9 |
| sibling filler | -0.482 | 0.054 | 0.62 |

**Exchange rate:** one strong look-alike adds as much as **7.9 doublings of length** (95% document-bootstrap interval 7.1 to 9.3, 500 draws); i.e. a document 245x longer (log-odds 8.72 for the look-alike at 8K / 1.10 per doubling without a look-alike).
With an interaction term: one doubling raises the log-odds by 1.099 (SE 0.091) without a look-alike and by -0.107 with a strong one.
