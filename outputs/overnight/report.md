# Overnight checks (analysis/overnight_checks.py)

Paper Exp 1 = code exp2, paper Exp 2 = code exp3. Rates in %. Intervals are 95%.

## A. Llama 3.3 70B at 128K (to-do item 5)

- Answers saved at 128K: 960 of 960 (per level 320 unanswerable and 160 answerable). Largest prompt 128,152 tokens against a window of 131,072 (2,920 tokens to spare). The runner skips any document that does not fit and never cuts one, so no prompt was truncated.
- Output truncated at 256 tokens: 2 of 960 answers.
- Made up answers without a look-alike: 238 of 320. Where the value came from: other_record 225, not_in_document 13 (other_record = the stated value belongs to another record in the document, so the model copies a real value from the wrong record).

### FP8 (main run) against bf16 (overnight rerun), Llama 3.3 70B at 128K

| level | FP8 made up | bf16 made up | Fisher p | FP8 accuracy | bf16 accuracy |
|---|---|---|---|---|---|
| none | 74.4 (238/320) | 68.1 (218/320) | 0.0969 | 49.4 | 50.6 |
| strong | 89.7 (287/320) | 85.3 (273/320) | 0.12 | 46.2 | 46.2 |

## B. Results by ladder (to-do item 7, 'is it just typo correction?')

Paper Exp 1 at 32K. The role ladder never changes a name, so a made up answer there is plainly wrong.

| model | ladder | none | weak | medium | strong | strong minus none (points) |
|---|---|---|---|---|---|---|
| Qwen3 4B | name | 0.0 | 0.8 | 30.8 | 80.8 | +80.8 |
| Qwen3 4B | role | 0.0 | 0.0 | 0.8 | 49.2 | +49.2 |
| Llama 3.1 8B | name | 0.0 | 0.8 | 24.2 | 91.7 | +91.7 |
| Llama 3.1 8B | role | 0.8 | 0.8 | 5.0 | 37.5 | +36.7 |
| Gemma 3 27B | name | 5.0 | 20.0 | 99.2 | 99.2 | +94.2 |
| Gemma 3 27B | role | 5.0 | 24.2 | 43.3 | 82.5 | +77.5 |
| Qwen3 30B A3B | name | 0.0 | 0.0 | 26.7 | 98.3 | +98.3 |
| Qwen3 30B A3B | role | 3.3 | 19.2 | 25.0 | 67.5 | +64.2 |
| Llama 3.3 70B | name | 0.0 | 1.7 | 51.7 | 100.0 | +100.0 |
| Llama 3.3 70B | role | 0.0 | 9.2 | 36.7 | 88.3 | +88.3 |
| Qwen3 Next 80B | name | 0.0 | 0.0 | 41.7 | 95.0 | +95.0 |
| Qwen3 Next 80B | role | 0.0 | 0.0 | 7.5 | 78.3 | +78.3 |
| GLM 4.5 Air 106B | name | 0.0 | 4.2 | 9.2 | 100.0 | +100.0 |
| GLM 4.5 Air 106B | role | 0.8 | 16.7 | 39.2 | 86.7 | +85.8 |

- Name ladder: strong minus none = 81 to 100 points.
- Role ladder: strong minus none = 37 to 88 points.

### Table 2 by ladder: strong look-alike at 32K vs no look-alike at the longest length

| model | ladder | strong, 32K | none, longest | gap (points) |
|---|---|---|---|---|
| Qwen3 4B | name | 80.8 | 0.0 (128K) | 80.8 |
| Qwen3 4B | role | 49.2 | 6.2 (128K) | 42.9 |
| Llama 3.1 8B | name | 91.7 | 8.1 (128K) | 83.5 |
| Llama 3.1 8B | role | 37.5 | 4.4 (128K) | 33.1 |
| Gemma 3 27B | name | 99.2 | 8.1 (64K) | 91.0 |
| Gemma 3 27B | role | 82.5 | 34.4 (64K) | 48.1 |
| Qwen3 30B A3B | name | 98.3 | 0.6 (128K) | 97.7 |
| Qwen3 30B A3B | role | 67.5 | 15.6 (128K) | 51.9 |
| Llama 3.3 70B | name | 100.0 | 61.9 (128K) | 38.1 |
| Llama 3.3 70B | role | 88.3 | 86.9 (128K) | 1.5 |
| Qwen3 Next 80B | name | 95.0 | 0.0 (128K) | 95.0 |
| Qwen3 Next 80B | role | 78.3 | 0.0 (128K) | 78.3 |
| GLM 4.5 Air 106B | name | 100.0 | 0.0 (128K) | 100.0 |
| GLM 4.5 Air 106B | role | 86.7 | 35.0 (128K) | 51.7 |

## C. Three-way outcome (to-do item 7)

Paper Exp 1, strong look-alike. 'Flagged' = a made up answer that also signals doubt or a mismatch (hedge words, or words like however, note, closest, similar, spelled, different). 'Silent' = all other made up answers. The headline effect is recomputed with flagged answers counted as refusals.

| model | ladder | refused | made up, flagged | made up, silent | silent only, strong minus none |
|---|---|---|---|---|---|
| Qwen3 4B | name | 19.2 | 2.5 | 78.3 | +78.3 |
| Qwen3 4B | role | 48.3 | 0.8 | 48.3 | +48.3 |
| Qwen3 4B | both | 33.8 | 1.7 | 63.3 | +63.3 |
| Llama 3.1 8B | name | 8.3 | 0.0 | 91.7 | +91.7 |
| Llama 3.1 8B | role | 62.5 | 0.0 | 37.5 | +36.7 |
| Llama 3.1 8B | both | 35.4 | 0.0 | 64.6 | +64.2 |
| Gemma 3 27B | name | 0.8 | 0.0 | 99.2 | +94.2 |
| Gemma 3 27B | role | 17.5 | 0.8 | 81.7 | +78.3 |
| Gemma 3 27B | both | 9.2 | 0.4 | 90.4 | +86.2 |
| Qwen3 30B A3B | name | 1.7 | 0.8 | 97.5 | +97.5 |
| Qwen3 30B A3B | role | 31.7 | 0.0 | 67.5 | +64.2 |
| Qwen3 30B A3B | both | 16.7 | 0.4 | 82.5 | +80.8 |
| Llama 3.3 70B | name | 0.0 | 0.8 | 99.2 | +99.2 |
| Llama 3.3 70B | role | 10.8 | 0.0 | 88.3 | +88.3 |
| Llama 3.3 70B | both | 5.4 | 0.4 | 93.8 | +93.8 |
| Qwen3 Next 80B | name | 5.0 | 3.3 | 91.7 | +91.7 |
| Qwen3 Next 80B | role | 21.7 | 0.8 | 77.5 | +77.5 |
| Qwen3 Next 80B | both | 13.3 | 2.1 | 84.6 | +84.6 |
| GLM 4.5 Air 106B | name | 0.0 | 0.0 | 100.0 | +100.0 |
| GLM 4.5 Air 106B | role | 13.3 | 0.0 | 86.7 | +85.8 |
| GLM 4.5 Air 106B | both | 6.7 | 0.0 | 93.3 | +92.9 |

## D. Exchange rate robustness (to-do item 3)

Exchange rate = doublings of length (no look-alike) that add as much log odds as one strong look-alike at 8K. 'undefined' means length has no clearly positive effect in that fit.

- leave one model out: 5.38 to 8.17 doublings over 7 fits.
- leave one family out: 4.98 to 8.78 doublings over 4 fits.
- leave one cell out: 5.53 to 7.94 doublings over 20 fits.
- Full fit: 5.85 doublings.
- Read: if the range is wide or often undefined, keep the exchange rate out of the abstract and lead with Table 2 (probability scale).

## E. Sibling filler as signal detection (to-do item 8)

Hit rate H = share of answerable questions answered correctly (same definition everywhere, fixes the 14.9 vs 16.4 mismatch). False alarm rate F = made up rate with a strong look-alike. d' = z(H) - z(F), c = -(z(H) + z(F))/2, rates clipped to [0.005, 0.995]. Intervals: document bootstrap.

| model | filler | H | F | d' [95%] | c [95%] |
|---|---|---|---|---|---|
| Qwen3 4B | unrelated | 90.9 | 73.8 | 0.70 [0.50, 0.94] | -0.99 [-1.10, -0.89] |
| Qwen3 4B | sibling | 74.5 | 54.1 | 0.56 [0.39, 0.74] | -0.38 [-0.47, -0.29] |
| Llama 3.1 8B | unrelated | 83.0 | 67.7 | 0.49 [0.27, 0.71] | -0.71 [-0.82, -0.59] |
| Llama 3.1 8B | sibling | 58.9 | 55.3 | 0.09 [-0.11, 0.29] | -0.18 [-0.28, -0.08] |
| Gemma 3 27B | unrelated | 79.0 | 93.8 | -0.73 [-0.99, -0.49] | -1.17 [-1.31, -1.05] |
| Gemma 3 27B | sibling | 68.5 | 90.2 | -0.81 [-1.06, -0.57] | -0.89 [-1.02, -0.77] |
| Qwen3 30B A3B | unrelated | 99.5 | 83.8 | 1.59 [1.30, 1.71] | -1.78 [-1.85, -1.63] |
| Qwen3 30B A3B | sibling | 97.8 | 82.0 | 1.10 [0.85, 1.39] | -1.47 [-1.61, -1.35] |
| Llama 3.3 70B | unrelated | 90.0 | 94.8 | -0.35 [-0.64, -0.12] | -1.46 [-1.59, -1.33] |
| Llama 3.3 70B | sibling | 72.0 | 82.2 | -0.34 [-0.54, -0.14] | -0.75 [-0.86, -0.65] |
| Qwen3 Next 80B | unrelated | 98.9 | 85.6 | 1.23 [0.97, 1.55] | -1.68 [-1.84, -1.54] |
| Qwen3 Next 80B | sibling | 92.0 | 77.5 | 0.65 [0.44, 0.88] | -1.08 [-1.20, -0.98] |
| GLM 4.5 Air 106B | unrelated | 100.0 | 94.0 | 1.02 [0.77, 1.23] | -2.06 [-2.19, -1.96] |
| GLM 4.5 Air 106B | sibling | 93.4 | 82.2 | 0.59 [0.37, 0.81] | -1.22 [-1.33, -1.12] |

- Qwen3 4B: accuracy loss 16.4 points, change in c +0.60, change in d' -0.14.
- Llama 3.1 8B: accuracy loss 24.1 points, change in c +0.53, change in d' -0.40.
- Gemma 3 27B: accuracy loss 10.5 points, change in c +0.28, change in d' -0.08.
- Qwen3 30B A3B: accuracy loss 1.7 points, change in c +0.31, change in d' -0.49.
- Llama 3.3 70B: accuracy loss 18.0 points, change in c +0.70, change in d' +0.01.
- Qwen3 Next 80B: accuracy loss 6.9 points, change in c +0.60, change in d' -0.58.
- GLM 4.5 Air 106B: accuracy loss 6.6 points, change in c +0.85, change in d' -0.44.

## F. Breaking lengths with document-level bootstrap intervals (to-do item 2)

Rule: first length whose interval lies fully above the 8K interval. Wilson treats the 320 questions per cell as independent; the bootstrap resamples whole documents (40 per cell).

| model | 8K | 32K | 64K | 128K | break (Wilson) | break (document bootstrap) |
|---|---|---|---|---|---|---|
| Qwen3 4B | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.9 [0.0, 2.2] | 3.1 [0.9, 5.6] | 128K | 128K |
| Llama 3.1 8B | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 6.2 [3.4, 9.4] | 128K | 128K |
| Gemma 3 27B | 0.6 [0.0, 1.6] | 5.9 [3.1, 8.8] | 21.2 [15.3, 27.5] | - | 32K | 32K |
| Qwen3 30B A3B | 0.6 [0.0, 1.9] | 2.5 [0.6, 4.7] | 3.4 [1.6, 5.6] | 8.1 [4.7, 12.2] | 128K | 128K |
| Llama 3.3 70B | 0.0 [0.0, 0.0] | 0.3 [0.0, 0.9] | 0.6 [0.0, 1.6] | 74.4 [65.0, 83.1] | 128K | 128K |
| Qwen3 Next 80B | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | none | none |
| GLM 4.5 Air 106B | 0.0 [0.0, 0.0] | 0.6 [0.0, 1.6] | 1.2 [0.3, 2.5] | 17.5 [9.4, 26.9] | 128K | 64K |

## G. RIKER2 per model, missing field questions (to-do item 12)

11 models tested at all three lengths. Difference = look-alike present minus none, in points.

| length | models with a significant positive difference | significant negative | not significant |
|---|---|---|---|
| 32K | 9 | 1 | 1 |
| 128K | 3 | 7 | 1 |
| 200K | 4 | 7 | 0 |

- Pooled logistic test (models as fixed effects): look-alike +1.31 (SE 0.03) log odds at 32K, change per doubling -0.68 (SE 0.01, z = -56.6). A clearly negative interaction means the look-alike effect shrinks with length in RIKER2.

## H. Prompt tokens per model and target length (before-submission item)

| model | 8K | 32K | 64K | 128K |
|---|---|---|---|---|
| Qwen3 4B | 9,569 | 38,106 | 76,169 | 152,260 |
| Llama 3.1 8B | 8,109 | 32,107 | 64,104 | 128,102 |
| Gemma 3 27B | 9,625 | 38,306 | 76,528 | - |
| Qwen3 30B A3B | 9,569 | 38,106 | 76,169 | 152,260 |
| Llama 3.3 70B | 8,109 | 32,107 | 64,104 | 128,102 |
| Qwen3 Next 80B | 9,569 | 38,106 | 76,169 | 152,260 |
| GLM 4.5 Air 106B | 8,294 | 32,956 | 65,845 | 130,476 |

## I. Is the no look-alike arm clean? (to-do item 4)

- paper Exp 1: 30 no look-alike documents, 2520 answers over all models, 0 with a look-alike value attached; 0 documents mix levels across their questions.
- paper Exp 2: 160 no look-alike documents, 12720 answers over all models, 0 with a look-alike value attached; 0 documents mix levels across their questions.
- Every document is one cell of the design grid (configs/experiments.yaml: lengths x ladders x levels x copies x filler x contexts), so all questions of a document share one level. Zeros above confirm that a no look-alike document has no look-alike for any question.

