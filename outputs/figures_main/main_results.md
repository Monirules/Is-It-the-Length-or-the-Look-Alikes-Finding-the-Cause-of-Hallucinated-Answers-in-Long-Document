# Main results (official scoring)

Models with results: Qwen3 4B, Llama 3.1 8B, Gemma 3 27B, Qwen3 30B-A3B, Llama 3.3 70B, Qwen3-Next 80B.

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

## Exp 2 stability: strong look-alike at T = 0.7, three seeds

| model | T=0 | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| Qwen3 4B | 65.0 [59-71] | 64.2 [58-70] | 61.7 [55-68] | 63.7 [57-70] |
| Llama 3.1 8B | 64.6 [58-70] | 69.2 [63-75] | 65.0 [59-71] | 65.8 [60-72] |
| Gemma 3 27B | 90.8 [87-94] | 90.0 [86-93] | 91.2 [87-94] | 90.8 [87-94] |
| Qwen3 30B-A3B | 82.9 [78-87] | 83.8 [79-88] | 82.9 [78-87] | 83.3 [78-88] |
| Llama 3.3 70B | 94.2 [90-96] | 96.2 [93-98] | 95.8 [93-98] | 94.2 [90-96] |
| Qwen3-Next 80B | 86.7 [82-90] | 86.2 [81-90] | 83.8 [79-88] | 83.8 [79-88] |

## Exp 3: length, with and without a strong look-alike (fillers pooled)

| model | none 8K | none 32K | none 64K | none 128K | strong 8K | strong 32K | strong 64K | strong 128K |
|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | 0.0 [0-1] | 0.0 [0-1] | 0.9 [0-3] | 3.1 [2-6] | 69.7 [64-74] | 57.5 [52-63] | 68.4 [63-73] | 60.0 [55-65] |
| Llama 3.1 8B | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 6.2 [4-9] | 62.5 [57-68] | 56.6 [51-62] | 62.8 [57-68] | 64.1 [59-69] |
| Gemma 3 27B | 0.6 [0-2] | 5.9 [4-9] | 21.2 [17-26] | - | 96.2 [94-98] | 92.8 [89-95] | 86.9 [83-90] | - |
| Qwen3 30B-A3B | 0.6 [0-2] | 2.5 [1-5] | 3.4 [2-6] | 8.1 [6-12] | 85.6 [81-89] | 83.8 [79-87] | 79.4 [75-83] | 82.8 [78-87] |
| Llama 3.3 70B | 0.0 [0-1] | 0.3 [0-2] | 0.6 [0-2] | 74.4 [69-79] | 89.7 [86-93] | 89.4 [86-92] | 85.3 [81-89] | 89.7 [86-93] |
| Qwen3-Next 80B | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 0.0 [0-1] | 86.6 [82-90] | 83.1 [79-87] | 80.3 [76-84] | 76.2 [71-81] |

Answer accuracy on questions WITH an answer, Exp 3 (checks that a model can still read at that length):

| model | 8K | 32K | 64K | 128K |
|---|---|---|---|---|
| Qwen3 4B | 95.0% | 87.2% | 83.4% | 65.3% |
| Llama 3.1 8B | 76.9% | 71.9% | 74.7% | 60.3% |
| Gemma 3 27B | 98.1% | 78.1% | 45.0% | - |
| Qwen3 30B-A3B | 100.0% | 99.4% | 98.1% | 97.2% |
| Llama 3.3 70B | 98.4% | 93.4% | 84.4% | 47.8% |
| Qwen3-Next 80B | 99.4% | 96.6% | 95.3% | 90.6% |

## Exp 3: filler type with a strong look-alike (all lengths)

| model | unrelated filler | sibling filler |
|---|---|---|
| Qwen3 4B | 73.8 [70-77] | 54.1 [50-58] |
| Llama 3.1 8B | 67.7 [64-71] | 55.3 [51-59] |
| Gemma 3 27B | 93.8 [91-96] | 90.2 [87-93] |
| Qwen3 30B-A3B | 83.8 [81-86] | 82.0 [79-85] |
| Llama 3.3 70B | 94.8 [93-96] | 82.2 [79-85] |
| Qwen3-Next 80B | 85.6 [83-88] | 77.5 [74-81] |

## Exp 4: copies of the same strong look-alike (32K)

| model | 1 copy | 2 copies | 4 copies | 8 copies |
|---|---|---|---|---|
| Qwen3 4B | 62.5 [55-70] | 76.9 [70-83] | 81.9 [75-87] | 83.1 [77-88] |
| Llama 3.1 8B | 58.8 [51-66] | 67.5 [60-74] | 61.3 [54-68] | 42.5 [35-50] |
| Gemma 3 27B | 96.2 [92-98] | 98.8 [96-100] | 100.0 [98-100] | 95.6 [91-98] |
| Qwen3 30B-A3B | 81.9 [75-87] | 90.0 [84-94] | 85.0 [79-90] | 81.9 [75-87] |
| Llama 3.3 70B | 94.4 [90-97] | 98.1 [95-99] | 95.6 [91-98] | 83.8 [77-89] |
| Qwen3-Next 80B | 86.9 [81-91] | 91.9 [87-95] | 93.8 [89-97] | 78.8 [72-84] |

## Logistic regression, Exp 3 (all Exp 3 answers), 14,720 no-answer questions

made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model

| term | log-odds | SE | odds ratio |
|---|---|---|---|
| one doubling of length | 0.135 | 0.018 | 1.14 |
| strong look-alike | 4.740 | 0.072 | 114.4 |
| sibling filler | -0.537 | 0.053 | 0.58 |

**Exchange rate:** one strong look-alike adds as much as **5.9 doublings of length** (log-odds 10.35 for the look-alike at 8K / 1.76 per doubling without a look-alike); i.e. a document 59x longer.
With an interaction term: one doubling raises the log-odds by 1.761 (SE 0.095) without a look-alike and by -0.071 with a strong one.

## Logistic regression, Exp 3 (without Llama 3.3 70B at 128K (its reading collapses there)), 14,080 no-answer questions

made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model

| term | log-odds | SE | odds ratio |
|---|---|---|---|
| one doubling of length | 0.001 | 0.020 | 1.00 |
| strong look-alike | 5.502 | 0.095 | 245.3 |
| sibling filler | -0.485 | 0.057 | 0.62 |

**Exchange rate:** one strong look-alike adds as much as **8.7 doublings of length** (log-odds 8.21 for the look-alike at 8K / 0.94 per doubling without a look-alike); i.e. a document 417x longer.
With an interaction term: one doubling raises the log-odds by 0.943 (SE 0.092) without a look-alike and by -0.081 with a strong one.
