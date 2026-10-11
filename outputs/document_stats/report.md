# Revision checks

Scored answers in the paper (seven models, bf16 audit excluded): 86,100. With the bf16 audit: 87,060.

All intervals are 95% percentile intervals from 2,000 bootstrap resamples of whole documents within a cell. Unpaired differences use independent document resamples and a document-level permutation test. Paired differences (same questions) resample documents jointly and use an exact McNemar test.

## A. Cell sizes (unanswerable questions and documents per cell, main runs)

| experiment | cell | unanswerable_min | unanswerable_max | documents_min | documents_max |
|---|---|---|---|---|---|
| Exp 1 | medium | 240 | 240 | 30 | 30 |
| Exp 1 | none | 240 | 240 | 30 | 30 |
| Exp 1 | strong | 240 | 240 | 30 | 30 |
| Exp 1 | weak | 240 | 240 | 30 | 30 |
| Exp 2 | none/128 | 160 | 320 | 20 | 40 |
| Exp 2 | none/32 | 320 | 320 | 40 | 40 |
| Exp 2 | none/64 | 320 | 320 | 40 | 40 |
| Exp 2 | none/8 | 320 | 320 | 40 | 40 |
| Exp 2 | strong/128 | 160 | 320 | 20 | 40 |
| Exp 2 | strong/32 | 320 | 320 | 40 | 40 |
| Exp 2 | strong/64 | 320 | 320 | 40 | 40 |
| Exp 2 | strong/8 | 320 | 320 | 40 | 40 |
| Exp 3 | 1 | 160 | 160 | 20 | 20 |
| Exp 3 | 2 | 160 | 160 | 20 | 20 |
| Exp 3 | 4 | 160 | 160 | 20 | 20 |
| Exp 3 | 8 | 160 | 160 | 20 | 20 |
| Exp 4 | lookalike/32 | 300 | 300 | 300 | 300 |
| Exp 4 | lookalike/8 | 300 | 300 | 300 | 300 |
| Exp 4 | random/32 | 300 | 300 | 300 | 300 |
| Exp 4 | random/8 | 300 | 300 | 300 | 300 |
| Exp 5 | strong | 160 | 160 | 20 | 20 |

## B. Exp 1, strong minus none (points)

| model | ladder | diff | diff_lo | diff_hi | p_doc_perm |
|---|---|---|---|---|---|
| Qwen3 4B | both | 65.0 | 56.2 | 73.8 | 0.0002 |
| Qwen3 4B | name | 80.8 | 73.3 | 88.3 | 0.0002 |
| Qwen3 4B | role | 49.2 | 38.3 | 60.0 | 0.0002 |
| Llama 3.1 8B | both | 64.2 | 54.2 | 74.6 | 0.0002 |
| Llama 3.1 8B | name | 91.7 | 87.5 | 95.8 | 0.0002 |
| Llama 3.1 8B | role | 36.7 | 30.0 | 43.3 | 0.0002 |
| Gemma 3 27B | both | 85.8 | 80.4 | 91.2 | 0.0002 |
| Gemma 3 27B | name | 94.2 | 89.2 | 98.3 | 0.0002 |
| Gemma 3 27B | role | 77.5 | 70.8 | 85.0 | 0.0002 |
| Qwen3 30B A3B | both | 81.2 | 74.2 | 87.9 | 0.0002 |
| Qwen3 30B A3B | name | 98.3 | 95.8 | 100.0 | 0.0002 |
| Qwen3 30B A3B | role | 64.2 | 56.7 | 72.5 | 0.0002 |
| Llama 3.3 70B | both | 94.2 | 90.8 | 97.5 | 0.0002 |
| Llama 3.3 70B | name | 100.0 | 100.0 | 100.0 | 0.0002 |
| Llama 3.3 70B | role | 88.3 | 82.5 | 94.2 | 0.0002 |
| Qwen3 Next 80B | both | 86.7 | 82.1 | 90.8 | 0.0002 |
| Qwen3 Next 80B | name | 95.0 | 90.8 | 98.3 | 0.0002 |
| Qwen3 Next 80B | role | 78.3 | 72.5 | 84.2 | 0.0002 |
| GLM 4.5 Air 106B | both | 92.9 | 87.9 | 97.1 | 0.0002 |
| GLM 4.5 Air 106B | name | 100.0 | 100.0 | 100.0 | 0.0002 |
| GLM 4.5 Air 106B | role | 85.8 | 78.3 | 92.5 | 0.0002 |

## C. Exp 2 breaking length, Wilson vs document bootstrap

| model | wilson | doc_bootstrap |
|---|---|---|
| Qwen3 4B | 128K | 128K |
| Llama 3.1 8B | 128K | 128K |
| Gemma 3 27B | 32K | 32K |
| Qwen3 30B A3B | 128K | 128K |
| Llama 3.3 70B | 128K | 128K |
| Qwen3 Next 80B | none | none |
| GLM 4.5 Air 106B | 128K | 64K |

## D. Same filler comparison inside Exp 2 (points)

| model | filler | longest | strong_32k | none_longest | gap_strong32_vs_none_longest | gap_strong32_vs_none_longest_lo | gap_strong32_vs_none_longest_hi | lookalike_effect_8k | lookalike_effect_longest | length_effect_none | length_effect_none_lo | length_effect_none_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | unrelated | 128K | 66.9 | 0.0 | 66.9 | 60 | 74.4 | 69.4 | 80.0 | 0.0 | 0.0 | 0.0 |
| Qwen3 4B | sibling | 128K | 48.1 | 6.2 | 41.9 | 30 | 53.1 | 70.0 | 33.8 | 6.2 | 2.5 | 10.6 |
| Llama 3.1 8B | unrelated | 128K | 63.7 | 10.6 | 53.1 | 39.4 | 67.5 | 65.6 | 61.3 | 10.6 | 6.2 | 15.6 |
| Llama 3.1 8B | sibling | 128K | 49.4 | 1.9 | 47.5 | 33.8 | 60.6 | 59.4 | 54.4 | 1.9 | 0.0 | 3.8 |
| Gemma 3 27B | unrelated | 64K | 92.5 | 22.5 | 70 | 61.3 | 78.1 | 97.5 | 68.1 | 21.9 | 15.6 | 28.8 |
| Gemma 3 27B | sibling | 64K | 93.1 | 20.0 | 73.1 | 61.9 | 83.7 | 93.8 | 63.1 | 19.4 | 9.4 | 30.6 |
| Qwen3 30B A3B | unrelated | 128K | 81.9 | 3.1 | 78.8 | 70 | 86.9 | 82.5 | 85.6 | 3.1 | 1.2 | 5.6 |
| Qwen3 30B A3B | sibling | 128K | 85.6 | 13.1 | 72.5 | 63.7 | 81.2 | 87.5 | 63.8 | 11.9 | 5.0 | 18.1 |
| Llama 3.3 70B | unrelated | 128K | 95.6 | 93.1 | 2.5 | -3.12 | 7.5 | 90.6 | 6.2 | 93.1 | 89.4 | 96.9 |
| Llama 3.3 70B | sibling | 128K | 83.1 | 55.6 | 27.5 | 13.7 | 42.5 | 88.8 | 24.4 | 55.6 | 41.2 | 68.8 |
| Qwen3 Next 80B | unrelated | 128K | 85.6 | 0.0 | 85.6 | 78.1 | 92.5 | 86.2 | 85.6 | 0.0 | 0.0 | 0.0 |
| Qwen3 Next 80B | sibling | 128K | 80.6 | 0.0 | 80.6 | 73.1 | 86.9 | 86.9 | 66.9 | 0.0 | 0.0 | 0.0 |
| GLM 4.5 Air 106B | unrelated | 64K | 95.0 | 0.0 | 95 | 90 | 98.8 | 93.8 | 93.1 | 0.0 | 0.0 | 0.0 |
| GLM 4.5 Air 106B | sibling | 128K | 90.6 | 17.5 | 73.1 | 62.5 | 83.1 | 90.0 | 48.1 | 17.5 | 8.8 | 26.2 |

## E. Exp 3 copies, 8 minus 1 copy

| model | c1 | c2 | c4 | c8 | diff_8_minus_1 | diff_lo | diff_hi | p_doc_perm | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | 62.5 | 76.9 | 81.9 | 83.1 | 20.6 | 6.9 | 34.4 | 0.0112 | 0.0672 |
| Llama 3.1 8B | 58.8 | 67.5 | 61.3 | 42.5 | -16.3 | -32.5 | 0.0 | 0.0874 | 0.437 |
| Gemma 3 27B | 96.2 | 98.8 | 100.0 | 95.6 | -0.6 | -5.6 | 4.4 | 1 | 1 |
| Qwen3 30B A3B | 81.9 | 90.0 | 85.0 | 81.9 | 0.0 | -10.0 | 10.6 | 1 | 1 |
| Llama 3.3 70B | 94.4 | 98.1 | 95.6 | 83.8 | -10.6 | -17.5 | -4.4 | 0.0068 | 0.0476 |
| Qwen3 Next 80B | 86.9 | 91.9 | 93.8 | 78.8 | -8.1 | -17.5 | 1.9 | 0.153 | 0.613 |
| GLM 4.5 Air 106B | 95.0 | 98.8 | 99.4 | 98.1 | 3.1 | -1.2 | 7.5 | 0.291 | 0.873 |

## F. Exp 4 Wikipedia

| model | passages | length | k | n | rate | boot_lo | boot_hi |
|---|---|---|---|---|---|---|---|
| Qwen3 4B | similar | 8 | 172 | 300 | 57.3 | 51.7 | 63.0 |
| Qwen3 4B | similar | 32 | 196 | 300 | 65.3 | 59.7 | 71.0 |
| Qwen3 4B | random | 8 | 0 | 300 | 0.0 | 0.0 | 0.0 |
| Qwen3 4B | random | 32 | 1 | 300 | 0.3 | 0.0 | 1.0 |
| Qwen3 4B | gold present | 8 | 142 | 300 | 47.3 | 41.7 | 53.3 |
| Llama 3.1 8B | similar | 8 | 144 | 300 | 48.0 | 42.3 | 53.7 |
| Llama 3.1 8B | similar | 32 | 167 | 300 | 55.7 | 50.0 | 61.3 |
| Llama 3.1 8B | random | 8 | 0 | 300 | 0.0 | 0.0 | 0.0 |
| Llama 3.1 8B | random | 32 | 1 | 300 | 0.3 | 0.0 | 1.0 |
| Llama 3.1 8B | gold present | 8 | 119 | 300 | 39.7 | 34.3 | 45.3 |
| Gemma 3 27B | similar | 8 | 246 | 300 | 82.0 | 77.7 | 86.3 |
| Gemma 3 27B | similar | 32 | 254 | 300 | 84.7 | 80.3 | 88.7 |
| Gemma 3 27B | random | 8 | 12 | 300 | 4.0 | 2.0 | 6.3 |
| Gemma 3 27B | random | 32 | 3 | 300 | 1.0 | 0.0 | 2.3 |
| Gemma 3 27B | gold present | 8 | 166 | 300 | 55.3 | 49.7 | 60.7 |
| Qwen3 30B A3B | similar | 8 | 232 | 300 | 77.3 | 72.7 | 82.0 |
| Qwen3 30B A3B | similar | 32 | 242 | 300 | 80.7 | 76.3 | 84.7 |
| Qwen3 30B A3B | random | 8 | 0 | 300 | 0.0 | 0.0 | 0.0 |
| Qwen3 30B A3B | random | 32 | 3 | 300 | 1.0 | 0.0 | 2.3 |
| Qwen3 30B A3B | gold present | 8 | 164 | 300 | 54.7 | 49.0 | 60.3 |
| Llama 3.3 70B | similar | 8 | 197 | 300 | 65.7 | 60.3 | 71.0 |
| Llama 3.3 70B | similar | 32 | 231 | 300 | 77.0 | 72.0 | 81.7 |
| Llama 3.3 70B | random | 8 | 6 | 300 | 2.0 | 0.7 | 3.7 |
| Llama 3.3 70B | random | 32 | 38 | 300 | 12.7 | 9.0 | 16.7 |
| Llama 3.3 70B | gold present | 8 | 191 | 300 | 63.7 | 58.0 | 69.0 |
| Qwen3 Next 80B | similar | 8 | 234 | 300 | 78.0 | 73.3 | 82.7 |
| Qwen3 Next 80B | similar | 32 | 261 | 300 | 87.0 | 83.0 | 90.7 |
| Qwen3 Next 80B | random | 8 | 3 | 300 | 1.0 | 0.0 | 2.3 |
| Qwen3 Next 80B | random | 32 | 6 | 300 | 2.0 | 0.7 | 3.7 |
| Qwen3 Next 80B | gold present | 8 | 179 | 300 | 59.7 | 54.3 | 65.0 |
| GLM 4.5 Air 106B | similar | 8 | 175 | 300 | 58.3 | 52.3 | 63.3 |
| GLM 4.5 Air 106B | similar | 32 | 184 | 300 | 61.3 | 56.0 | 66.7 |
| GLM 4.5 Air 106B | random | 8 | 5 | 300 | 1.7 | 0.3 | 3.3 |
| GLM 4.5 Air 106B | random | 32 | 16 | 300 | 5.3 | 3.0 | 7.7 |
| GLM 4.5 Air 106B | gold present | 8 | 145 | 300 | 48.3 | 42.7 | 53.7 |

## G. Paired comparisons

| comparison | model | n | docs | rate_a | rate_b | diff | diff_lo | diff_hi | a_only | b_only | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Exp 5: 12 per call minus 1 per call, made up | Qwen3 4B | 160 | 20 | 75.6 | 63.1 | 12.5 | 4.4 | 20.0 | 34 | 14 | 0.00552 |
| Exp 5: 12 per call minus 1 per call, accuracy | Qwen3 4B | 80 | 20 | 78.8 | 92.5 | -13.8 | -23.8 | -5.0 | 0 | 11 | 0.000977 |
| Exp 5: 12 per call minus 1 per call, made up | Llama 3.1 8B | 160 | 20 | 95.0 | 57.5 | 37.5 | 25.6 | 50.0 | 61 | 1 | 2.73e-17 |
| Exp 5: 12 per call minus 1 per call, accuracy | Llama 3.1 8B | 80 | 20 | 88.8 | 77.5 | 11.2 | 0.0 | 21.2 | 14 | 5 | 0.0636 |
| Llama 3.3 70B 128K: FP8 minus bf16, made up, none | Llama 3.3 70B | 320 | 40 | 74.4 | 68.1 | 6.2 | 1.6 | 10.9 | 29 | 9 | 0.00166 |
| Llama 3.3 70B 128K: FP8 minus bf16, made up, strong | Llama 3.3 70B | 320 | 40 | 89.7 | 85.3 | 4.4 | 1.6 | 7.8 | 16 | 2 | 0.00131 |
| Llama 3.3 70B 128K: FP8 minus bf16, accuracy | Llama 3.3 70B | 320 | 80 | 47.8 | 48.4 | -0.6 | -3.8 | 2.5 | 13 | 15 | 0.851 |
| Strict minus normal prompt, made up (strong, 32K) | Qwen3 4B | 240 | 30 | 49.6 | 65.0 | -15.4 | -21.2 | -9.6 | 10 | 47 | 7.51e-07 |
| Strict minus normal prompt, accuracy (strong, 32K) | Qwen3 4B | 120 | 30 | 90.0 | 95.8 | -5.8 | -10.0 | -1.7 | 1 | 8 | 0.0391 |
| Strict minus normal prompt, made up (strong, 32K) | Llama 3.1 8B | 240 | 30 | 57.1 | 64.6 | -7.5 | -11.7 | -2.9 | 10 | 28 | 0.0051 |
| Strict minus normal prompt, accuracy (strong, 32K) | Llama 3.1 8B | 120 | 30 | 68.3 | 75.0 | -6.7 | -13.3 | -0.8 | 5 | 13 | 0.0963 |
| Strict minus normal prompt, made up (strong, 32K) | Gemma 3 27B | 240 | 30 | 77.9 | 90.8 | -12.9 | -19.2 | -7.1 | 1 | 32 | 7.92e-09 |
| Strict minus normal prompt, accuracy (strong, 32K) | Gemma 3 27B | 120 | 30 | 70.0 | 82.5 | -12.5 | -17.5 | -7.5 | 0 | 15 | 6.1e-05 |
| Strict minus normal prompt, made up (strong, 32K) | Qwen3 30B A3B | 240 | 30 | 82.1 | 82.9 | -0.8 | -4.2 | 2.5 | 10 | 12 | 0.832 |
| Strict minus normal prompt, accuracy (strong, 32K) | Qwen3 30B A3B | 120 | 30 | 96.7 | 100.0 | -3.3 | -6.7 | -0.8 | 0 | 4 | 0.125 |
| Strict minus normal prompt, made up (strong, 32K) | Llama 3.3 70B | 240 | 30 | 67.5 | 94.2 | -26.7 | -35.0 | -19.6 | 0 | 64 | 1.08e-19 |
| Strict minus normal prompt, accuracy (strong, 32K) | Llama 3.3 70B | 120 | 30 | 85.8 | 97.5 | -11.7 | -17.5 | -6.7 | 0 | 14 | 0.000122 |
| Strict minus normal prompt, made up (strong, 32K) | Qwen3 Next 80B | 240 | 30 | 53.8 | 86.7 | -32.9 | -38.8 | -26.2 | 1 | 80 | 6.78e-23 |
| Strict minus normal prompt, accuracy (strong, 32K) | Qwen3 Next 80B | 120 | 30 | 95.0 | 100.0 | -5.0 | -10.0 | -1.7 | 0 | 6 | 0.0312 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Qwen3 4B | 240 | 30 | 64.2 | 65.0 | -0.8 | -3.3 | 1.7 | 6 | 8 | 0.791 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Qwen3 4B | 240 | 30 | 61.7 | 65.0 | -3.3 | -6.2 | 0.0 | 4 | 12 | 0.0768 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Qwen3 4B | 240 | 30 | 63.8 | 65.0 | -1.2 | -4.6 | 2.1 | 7 | 10 | 0.629 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Llama 3.1 8B | 240 | 30 | 69.2 | 64.6 | 4.6 | 1.7 | 7.5 | 14 | 3 | 0.0127 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Llama 3.1 8B | 240 | 30 | 65.0 | 64.6 | 0.4 | -3.3 | 4.6 | 13 | 12 | 1 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Llama 3.1 8B | 240 | 30 | 65.8 | 64.6 | 1.2 | -2.9 | 5.8 | 16 | 13 | 0.711 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Gemma 3 27B | 240 | 30 | 90.0 | 90.8 | -0.8 | -3.3 | 1.2 | 2 | 4 | 0.688 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Gemma 3 27B | 240 | 30 | 91.2 | 90.8 | 0.4 | -0.8 | 1.7 | 2 | 1 | 1 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Gemma 3 27B | 240 | 30 | 90.8 | 90.8 | 0.0 | -1.7 | 1.7 | 2 | 2 | 1 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Qwen3 30B A3B | 240 | 30 | 83.8 | 82.9 | 0.8 | -1.2 | 3.3 | 6 | 4 | 0.754 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Qwen3 30B A3B | 240 | 30 | 82.9 | 82.9 | 0.0 | -2.9 | 2.9 | 8 | 8 | 1 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Qwen3 30B A3B | 240 | 30 | 83.3 | 82.9 | 0.4 | -2.9 | 3.3 | 9 | 8 | 1 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Llama 3.3 70B | 240 | 30 | 96.2 | 94.2 | 2.1 | -0.4 | 4.6 | 9 | 4 | 0.267 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Llama 3.3 70B | 240 | 30 | 95.8 | 94.2 | 1.7 | -0.4 | 4.2 | 6 | 2 | 0.289 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Llama 3.3 70B | 240 | 30 | 94.2 | 94.2 | 0.0 | -2.5 | 2.5 | 4 | 4 | 1 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | Qwen3 Next 80B | 240 | 30 | 86.2 | 86.7 | -0.4 | -2.9 | 2.1 | 6 | 7 | 1 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | Qwen3 Next 80B | 240 | 30 | 83.8 | 86.7 | -2.9 | -5.8 | -0.4 | 4 | 11 | 0.118 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | Qwen3 Next 80B | 240 | 30 | 83.8 | 86.7 | -2.9 | -5.0 | -0.8 | 2 | 9 | 0.0654 |
| T=0.7 s1 minus T=0, made up (strong, 32K) | GLM 4.5 Air 106B | 240 | 30 | 92.1 | 93.3 | -1.2 | -3.3 | 0.4 | 1 | 4 | 0.375 |
| T=0.7 s2 minus T=0, made up (strong, 32K) | GLM 4.5 Air 106B | 240 | 30 | 91.2 | 93.3 | -2.1 | -6.2 | 2.1 | 8 | 13 | 0.383 |
| T=0.7 s3 minus T=0, made up (strong, 32K) | GLM 4.5 Air 106B | 240 | 30 | 90.0 | 93.3 | -3.3 | -7.1 | -0.4 | 3 | 11 | 0.0574 |

## H. Answer or refuse decision (corrected signal detection)

Hit rate = share of answerable questions the model answers at all (correct or wrong value). False alarm rate = share of unanswerable strong look-alike questions it answers. Both from the same documents, unscorable answers removed. Correctness is reported separately.

| condition | model | answer_rate_answerable | answer_rate_unanswerable | d_prime | d_lo | d_hi | c | c_lo | c_hi | correct_given_answered |
|---|---|---|---|---|---|---|---|---|---|---|
| Exp 2, unrelated filler | Qwen3 4B | 92.19 | 74.10 | 0.77 | 0.52 | 1.06 | -1.03 | -1.20 | -0.88 | 97.63 |
| Exp 2, sibling filler | Qwen3 4B | 82.28 | 54.83 | 0.80 | 0.60 | 1.00 | -0.52 | -0.64 | -0.41 | 93.46 |
| Exp 1 strong, normal prompt | Qwen3 4B | 95.83 | 65.82 | 1.32 | 1.00 | 1.89 | -1.07 | -1.38 | -0.85 | 100.00 |
| Exp 1 strong, strict prompt | Qwen3 4B | 90.00 | 49.79 | 1.29 | 1.03 | 1.59 | -0.64 | -0.83 | -0.48 | 100.00 |
| Exp 2, unrelated filler | Llama 3.1 8B | 78.06 | 67.87 | 0.31 | 0.15 | 0.46 | -0.62 | -0.79 | -0.45 | 96.79 |
| Exp 2, sibling filler | Llama 3.1 8B | 65.52 | 55.66 | 0.26 | 0.09 | 0.43 | -0.27 | -0.42 | -0.14 | 90.91 |
| Exp 1 strong, normal prompt | Llama 3.1 8B | 76.67 | 64.58 | 0.35 | 0.13 | 0.61 | -0.55 | -0.83 | -0.28 | 97.83 |
| Exp 1 strong, strict prompt | Llama 3.1 8B | 71.19 | 57.08 | 0.38 | 0.17 | 0.61 | -0.37 | -0.63 | -0.13 | 97.62 |
| Exp 2, unrelated filler | Gemma 3 27B | 95.00 | 93.75 | 0.11 | -0.22 | 0.50 | -1.59 | -1.81 | -1.43 | 82.89 |
| Exp 2, sibling filler | Gemma 3 27B | 97.08 | 90.40 | 0.59 | 0.28 | 1.12 | -1.60 | -1.90 | -1.42 | 67.38 |
| Exp 1 strong, normal prompt | Gemma 3 27B | 96.67 | 90.83 | 0.50 | 0.08 | 1.16 | -1.58 | -1.95 | -1.38 | 85.34 |
| Exp 1 strong, strict prompt | Gemma 3 27B | 85.83 | 77.92 | 0.30 | 0.05 | 0.57 | -0.92 | -1.21 | -0.70 | 81.55 |
| Exp 2, unrelated filler | Qwen3 30B A3B | 100.00 | 83.75 | 1.59 | 1.46 | 1.73 | -1.78 | -1.85 | -1.71 | 99.69 |
| Exp 2, sibling filler | Qwen3 30B A3B | 99.06 | 82.29 | 1.42 | 1.02 | 1.74 | -1.64 | -1.78 | -1.48 | 99.37 |
| Exp 1 strong, normal prompt | Qwen3 30B A3B | 100.00 | 83.26 | 1.61 | 1.30 | 1.86 | -1.77 | -1.93 | -1.65 | 100.00 |
| Exp 1 strong, strict prompt | Qwen3 30B A3B | 100.00 | 82.08 | 1.66 | 1.34 | 1.89 | -1.75 | -1.91 | -1.63 | 96.67 |
| Exp 2, unrelated filler | Llama 3.3 70B | 97.81 | 95.14 | 0.36 | 0.08 | 0.77 | -1.84 | -2.10 | -1.67 | 91.69 |
| Exp 2, sibling filler | Llama 3.3 70B | 89.87 | 83.10 | 0.32 | 0.11 | 0.54 | -1.12 | -1.27 | -0.98 | 80.28 |
| Exp 1 strong, normal prompt | Llama 3.3 70B | 100.00 | 94.56 | 0.97 | 0.54 | 1.27 | -2.09 | -2.31 | -1.94 | 97.50 |
| Exp 1 strong, strict prompt | Llama 3.3 70B | 88.33 | 67.50 | 0.74 | 0.47 | 1.01 | -0.82 | -1.09 | -0.61 | 97.17 |
| Exp 2, unrelated filler | Qwen3 Next 80B | 99.06 | 85.62 | 1.29 | 0.97 | 1.57 | -1.71 | -1.87 | -1.52 | 99.68 |
| Exp 2, sibling filler | Qwen3 Next 80B | 92.48 | 78.11 | 0.66 | 0.46 | 0.92 | -1.11 | -1.27 | -0.97 | 99.66 |
| Exp 1 strong, normal prompt | Qwen3 Next 80B | 100.00 | 86.67 | 1.47 | 1.25 | 1.66 | -1.84 | -1.95 | -1.75 | 100.00 |
| Exp 1 strong, strict prompt | Qwen3 Next 80B | 95.83 | 53.75 | 1.64 | 1.33 | 2.19 | -0.91 | -1.23 | -0.71 | 99.13 |
| Exp 2, unrelated filler | GLM 4.5 Air 106B | 100.00 | 93.96 | 1.02 | 0.77 | 1.23 | -2.06 | -2.19 | -1.96 | 100.00 |
| Exp 2, sibling filler | GLM 4.5 Air 106B | 97.19 | 82.83 | 0.96 | 0.67 | 1.37 | -1.43 | -1.65 | -1.26 | 95.50 |

## I. Automatic three-way split (strong look-alike, Exp 1)

| model | ladder | n_strong | refused | made_up_flagged | made_up_silent | effect_all | effect_silent_only |
|---|---|---|---|---|---|---|---|
| Qwen3 4B | name | 120 | 19.2 | 2.5 | 78.3 | 80.8 | 78.3 |
| Qwen3 4B | role | 120 | 48.3 | 0.833 | 48.3 | 49.2 | 48.3 |
| Llama 3.1 8B | name | 120 | 8.3 | 0 | 91.7 | 91.7 | 91.7 |
| Llama 3.1 8B | role | 120 | 62.5 | 0 | 37.5 | 36.7 | 36.7 |
| Gemma 3 27B | name | 120 | 0.8 | 0 | 99.2 | 94.2 | 94.2 |
| Gemma 3 27B | role | 120 | 17.5 | 0.833 | 81.7 | 77.5 | 78.3 |
| Qwen3 30B A3B | name | 120 | 1.7 | 0.833 | 97.5 | 98.3 | 97.5 |
| Qwen3 30B A3B | role | 120 | 31.7 | 0 | 67.5 | 64.2 | 64.2 |
| Llama 3.3 70B | name | 120 | 0.0 | 0.833 | 99.2 | 100.0 | 99.2 |
| Llama 3.3 70B | role | 120 | 10.8 | 0 | 88.3 | 88.3 | 88.3 |
| Qwen3 Next 80B | name | 120 | 5.0 | 3.33 | 91.7 | 95.0 | 91.7 |
| Qwen3 Next 80B | role | 120 | 21.7 | 0.833 | 77.5 | 78.3 | 77.5 |
| GLM 4.5 Air 106B | name | 120 | 0.0 | 0 | 100 | 100.0 | 100.0 |
| GLM 4.5 Air 106B | role | 120 | 13.3 | 0 | 86.7 | 85.8 | 85.8 |

## J. Audit sheets

- audit_nullscale_sheet.csv: 201 Exp 1 strong look-alike answers (12 made up and 3 refusals per model and ladder), shuffled, model hidden. Key in audit_nullscale_key.csv.
- audit_wikipedia_sheet.csv: 105 Exp 4 made up answers with similar passages (up to 15 per model). Key in audit_wikipedia_key.csv.

Labels for audit_nullscale_sheet.csv, column label:
- R: refuses, states no value for the asked record
- W: states the look-alike's value but explicitly says it belongs to a different name, building or year
- U: states a value as the answer without any warning (unsupported answer)
- O: other or unclear

Labels for audit_wikipedia_sheet.csv, column answer_in_passages:
- yes: the passages state the answer, also in other words, so the question was not truly unanswerable
- no: the passages do not state it
- unsure
Run python -m analysis.nq_context_check --data <folder with exp6/docs> first; it marks items whose true answer string appears in the passages.
