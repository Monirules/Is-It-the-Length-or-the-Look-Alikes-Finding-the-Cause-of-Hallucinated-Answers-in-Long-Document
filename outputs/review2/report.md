# Review 2 checks

All intervals resample whole documents (2,000 draws). Unpaired tests are document permutation tests.

## A. Per model effects in Experiment 2 (points)

lookalike_X = strong minus none at length X. length_none = none at the longest length minus none at 8K. interaction = lookalike_longest minus lookalike_8k (negative means the look-alike effect shrinks with length).

| model | filler | longest | lookalike_8k | lookalike_8k_lo | lookalike_8k_hi | lookalike_longest | lookalike_longest_lo | lookalike_longest_hi | length_none | length_none_lo | length_none_hi | length_none_p | interaction | interaction_lo | interaction_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | pooled | 128K | 69.7 | 61.9 | 77.8 | 56.9 | 48.8 | 64.7 | 3.1 | 0.9 | 5.3 | 0.0 | -12.8 | -24.4 | -0.9 |
| Qwen3 4B | unrelated | 128K | 69.4 | 55.6 | 82.5 | 80.0 | 73.1 | 86.9 | 0.0 | 0.0 | 0.0 | 1.0 | 10.6 | -4.4 | 25.0 |
| Qwen3 4B | sibling | 128K | 70.0 | 60.6 | 79.4 | 33.8 | 25.0 | 42.5 | 6.2 | 2.5 | 10.6 | 0.0 | -36.2 | -48.8 | -23.1 |
| Llama 3.1 8B | pooled | 128K | 62.5 | 52.8 | 71.2 | 57.8 | 49.4 | 66.2 | 6.2 | 3.8 | 9.4 | 0.0 | -4.7 | -16.9 | 7.5 |
| Llama 3.1 8B | unrelated | 128K | 65.6 | 52.5 | 78.1 | 61.3 | 48.8 | 72.5 | 10.6 | 6.2 | 15.6 | 0.0 | -4.4 | -21.9 | 13.1 |
| Llama 3.1 8B | sibling | 128K | 59.4 | 46.2 | 71.9 | 54.4 | 44.4 | 63.8 | 1.9 | 0.0 | 3.8 | 0.2 | -5.0 | -21.3 | 10.6 |
| Gemma 3 27B | pooled | 64K | 95.6 | 93.4 | 97.8 | 65.6 | 58.1 | 73.1 | 20.6 | 14.4 | 27.5 | 0.0 | -30.0 | -37.8 | -21.9 |
| Gemma 3 27B | unrelated | 64K | 97.5 | 95.0 | 99.4 | 68.1 | 59.4 | 76.9 | 21.9 | 15.0 | 28.7 | 0.0 | -29.4 | -38.1 | -20.6 |
| Gemma 3 27B | sibling | 64K | 93.8 | 90.0 | 96.9 | 63.1 | 50.6 | 75.0 | 19.4 | 10.0 | 30.6 | 0.0 | -30.6 | -42.5 | -18.1 |
| Qwen3 30B A3B | pooled | 128K | 85.0 | 80.3 | 89.7 | 74.7 | 67.8 | 80.6 | 7.5 | 3.4 | 11.2 | 0.0 | -10.3 | -18.4 | -2.8 |
| Qwen3 30B A3B | unrelated | 128K | 82.5 | 74.4 | 90.0 | 85.6 | 79.4 | 91.3 | 3.1 | 1.2 | 5.6 | 0.1 | 3.1 | -6.2 | 12.5 |
| Qwen3 30B A3B | sibling | 128K | 87.5 | 82.5 | 91.9 | 63.8 | 53.1 | 74.4 | 11.9 | 5.0 | 18.8 | 0.0 | -23.7 | -35.0 | -11.9 |
| Llama 3.3 70B | pooled | 128K | 89.7 | 85.9 | 93.4 | 15.3 | 5.0 | 25.9 | 74.4 | 64.7 | 82.8 | 0.0 | -74.4 | -85.9 | -62.5 |
| Llama 3.3 70B | unrelated | 128K | 90.6 | 83.8 | 96.2 | 6.2 | 2.5 | 10.6 | 93.1 | 88.8 | 96.9 | 0.0 | -84.4 | -91.9 | -76.2 |
| Llama 3.3 70B | sibling | 128K | 88.8 | 84.4 | 93.1 | 24.4 | 9.4 | 40.0 | 55.6 | 41.2 | 68.8 | 0.0 | -64.4 | -80.0 | -48.1 |
| Qwen3 Next 80B | pooled | 128K | 86.6 | 81.9 | 90.9 | 76.2 | 69.1 | 82.5 | 0.0 | 0.0 | 0.0 | 1.0 | -10.3 | -18.1 | -2.2 |
| Qwen3 Next 80B | unrelated | 128K | 86.2 | 79.4 | 91.9 | 85.6 | 80.6 | 90.6 | 0.0 | 0.0 | 0.0 | 1.0 | -0.6 | -8.7 | 7.5 |
| Qwen3 Next 80B | sibling | 128K | 86.9 | 80.6 | 93.1 | 66.9 | 55.6 | 77.5 | 0.0 | 0.0 | 0.0 | 1.0 | -20.0 | -32.5 | -7.5 |
| GLM 4.5 Air 106B | pooled | 128K | 91.9 | 89.4 | 94.4 | 48.1 | 35.0 | 60.6 | 17.5 | 8.8 | 26.3 | 0.0 | -43.8 | -58.4 | -29.7 |
| GLM 4.5 Air 106B | unrelated | 64K | 93.8 | 89.4 | 97.5 | 93.1 | 88.1 | 97.5 | 0.0 | 0.0 | 0.0 | 1.0 | -0.6 | -6.9 | 5.0 |
| GLM 4.5 Air 106B | sibling | 128K | 90.0 | 86.9 | 93.1 | 48.1 | 33.1 | 61.9 | 17.5 | 9.4 | 26.9 | 0.0 | -41.9 | -56.2 | -28.1 |

## B. Two stage mixed model (per model logistic fits with document clustered errors, pooled by DerSimonian and Laird random effects)

| model | beta_length_no_lookalike | se_length_no_lookalike | beta_strong_at_8k | se_strong_at_8k | beta_length_x_strong | se_length_x_strong | beta_length_additive | se_length_additive | beta_strong_additive | se_strong_additive | n | documents |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | 1.002 | 0.241 | 8.401 | 0.679 | -1.077 | 0.246 | -0.043 | 0.056 | 5.230 | 0.353 | 2560 | 320 |
| Llama 3.1 8B | 1.715 | 0.184 | 10.721 | 0.540 | -1.683 | 0.189 | 0.087 | 0.051 | 5.221 | 0.279 | 2560 | 320 |
| Gemma 3 27B | 1.255 | 0.197 | 8.399 | 0.565 | -1.693 | 0.228 | 0.215 | 0.089 | 4.777 | 0.220 | 1920 | 240 |
| Qwen3 30B A3B | 0.611 | 0.174 | 6.704 | 0.597 | -0.682 | 0.185 | 0.036 | 0.056 | 4.857 | 0.192 | 2560 | 320 |
| Llama 3.3 70B | 4.547 | 0.276 | 19.404 | 1.042 | -4.567 | 0.290 | 0.693 | 0.094 | 4.340 | 0.260 | 2560 | 320 |
| Qwen3 Next 80B | -1.203 | 0.064 | 8.480 | 0.245 | 1.019 | 0.075 | -0.188 | 0.055 | 9.286 | 0.157 | 2560 | 320 |
| GLM 4.5 Air 106B | 2.039 | 0.321 | 12.515 | 1.114 | -2.403 | 0.329 | -0.087 | 0.091 | 5.526 | 0.329 | 2240 | 280 |

| term | pooled | se | lo | hi | between_model_sd | Q | prediction_lo | prediction_hi |
|---|---|---|---|---|---|---|---|---|
| beta_length_no_lookalike | 1.41 | 0.751 | -0.056 | 2.886 | 1.973 | 801.198 | -2.72 | 5.55 |
| beta_strong_at_8k | 10.5 | 1.033 | 8.481 | 12.528 | 2.634 | 140.979 | 4.96 | 16.1 |
| beta_length_x_strong | -1.57 | 0.732 | -3.007 | -0.139 | 1.922 | 653.461 | -5.6 | 2.46 |
| beta_length_additive | 0.0939 | 0.087 | -0.076 | 0.264 | 0.218 | 74.054 | -0.367 | 0.554 |
| beta_strong_additive | 5.61 | 0.856 | 3.931 | 7.288 | 2.250 | 553.391 | 0.89 | 10.3 |

Exchange rate from pooled terms: 7.42 doublings. Across models the length slope without a look-alike is not positive in 25% of draws from the random effects distribution, and the ratio ranges from -62.0 to 67.2 (2.5 and 97.5 percentiles), so the exchange rate is not identified across models.

## C. RIKER2 near matches per trap question

| length | level | questions | share_with_lookalike | mean_lookalikes | median_lookalikes | share_two_or_more | mean_partial_matches | mean_lookalikes_plus_partial |
|---|---|---|---|---|---|---|---|---|
| 32 | L11 | 63 | 100.00 | 1.24 | 1.00 | 23.81 | 3.08 | 4.32 |
| 128 | L11 | 90 | 100.00 | 1.22 | 1.00 | 22.22 | 7.10 | 8.32 |
| 200 | L11 | 116 | 100.00 | 1.22 | 1.00 | 21.55 | 11.13 | 12.34 |
| 32 | L12 | 63 | 26.98 | 0.35 | 0.00 | 6.35 | 2.06 | 2.41 |
| 128 | L12 | 90 | 24.44 | 0.34 | 0.00 | 7.78 | 5.03 | 5.38 |
| 200 | L12 | 117 | 22.22 | 0.31 | 0.00 | 7.69 | 6.18 | 6.49 |
| 32 | all | 126 | 63.49 | 0.79 | 1.00 | 15.08 | 2.57 | 3.37 |
| 128 | all | 180 | 62.22 | 0.78 | 1.00 | 15.00 | 6.07 | 6.85 |
| 200 | all | 233 | 60.94 | 0.76 | 1.00 | 14.59 | 8.64 | 9.40 |

## D. Heuristic model fit and predictions (no look-alike fabrication, %)

p0 is the per 1K token chance of a wrong accept, p_s the chance for the strong look-alike. Predictions at 16K, 96K and 112K are made before any run.

| model | p0_per_1k_tokens | p_s | pred_none_8k | obs_none_8k | pred_none_16k | pred_none_32k | obs_none_32k | pred_none_64k | obs_none_64k | pred_none_96k | pred_none_112k | pred_none_128k | obs_none_128k | pred_break_16k | pred_break_96k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | 0.000173 | 0.631 | 0.139 | 0.000 | 0.277 | 0.553 | 0.000 | 1.1 | 0.938 | 1.65 | 1.92 | 2.2 | 3.125 | False | False |
| Llama 3.1 8B | 0.000276 | 0.611 | 0.221 | 0.000 | 0.441 | 0.88 | 0.000 | 1.75 | 0.000 | 2.62 | 3.05 | 3.47 | 6.250 | False | True |
| Gemma 3 27B | 0.0028 | 0.911 | 2.22 | 0.625 | 4.39 | 8.59 | 5.938 | 16.4 | 21.250 | 23.6 | 27 | 30.2 |  | True | True |
| Qwen3 30B A3B | 0.000645 | 0.821 | 0.514 | 0.625 | 1.03 | 2.04 | 2.500 | 4.04 | 3.438 | 6 | 6.97 | 7.92 | 8.125 | False | True |
| Llama 3.3 70B | 0.00407 | 0.861 | 3.21 | 0.000 | 6.32 | 12.2 | 0.312 | 23 | 0.625 | 32.4 | 36.7 | 40.7 | 74.375 | True | True |
| Qwen3 Next 80B | 0 | 0.811 | 0 | 0.000 | 0 | 0 | 0.000 | 0 | 0.000 | 0 | 0 | 0 | 0.000 | False | False |
| GLM 4.5 Air 106B | 0.000604 | 0.871 | 0.482 | 0.000 | 0.963 | 1.92 | 0.625 | 3.79 | 1.250 | 5.64 | 6.55 | 7.45 | 17.500 | False | True |

## E. Experiment 8 control: same eight extra records, none matching the asked key

| model | ladder | none | none_lo | none_hi | none_docs | decoy | decoy_lo | decoy_hi | decoy_docs | strong | strong_lo | strong_hi | strong_docs | decoy_minus_none | decoy_minus_none_lo | decoy_minus_none_hi | decoy_minus_none_p | strong_minus_decoy | strong_minus_decoy_lo | strong_minus_decoy_hi | strong_minus_decoy_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3 4B | both | 0.0 | 0.0 | 0.0 | 30 | 0.0 | 0.0 | 0.0 | 30 | 63.7 | 56.7 | 70.4 | 30 | 0.0 | 0.0 | 0.0 | 1.0 | 63.7 | 56.2 | 71.2 | 0.0 |
| Qwen3 4B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 75.0 | 67.5 | 82.5 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 75.0 | 67.5 | 82.5 | 0.0 |
| Qwen3 4B | role | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 52.5 | 42.5 | 61.7 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 52.5 | 43.3 | 61.7 | 0.0 |
| Llama 3.1 8B | both | 0.0 | 0.0 | 0.0 | 30 | 0.0 | 0.0 | 0.0 | 30 | 58.3 | 47.5 | 68.8 | 30 | 0.0 | 0.0 | 0.0 | 1.0 | 58.3 | 48.3 | 68.8 | 0.0 |
| Llama 3.1 8B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 82.5 | 75.0 | 89.2 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 82.5 | 75.0 | 89.2 | 0.0 |
| Llama 3.1 8B | role | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 34.2 | 25.8 | 43.3 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 34.2 | 25.8 | 43.3 | 0.0 |
| Gemma 3 27B | both | 5.8 | 2.9 | 9.6 | 30 | 5.8 | 2.9 | 9.2 | 30 | 92.5 | 89.2 | 95.8 | 30 | 0.0 | -5.0 | 4.6 | 1.0 | 86.7 | 82.1 | 91.2 | 0.0 |
| Gemma 3 27B | name | 5.0 | 0.8 | 10.8 | 15 | 0.8 | 0.0 | 2.5 | 15 | 99.2 | 97.5 | 100.0 | 15 | -4.2 | -10.0 | 0.0 | 0.3 | 98.3 | 95.8 | 100.0 | 0.0 |
| Gemma 3 27B | role | 6.7 | 2.5 | 11.7 | 15 | 10.8 | 5.8 | 15.9 | 15 | 85.8 | 81.7 | 90.8 | 15 | 4.2 | -2.5 | 10.8 | 0.4 | 75.0 | 68.3 | 81.7 | 0.0 |
| Qwen3 30B A3B | both | 0.0 | 0.0 | 0.0 | 30 | 0.8 | 0.0 | 2.1 | 30 | 80.4 | 73.8 | 86.7 | 30 | 0.8 | 0.0 | 2.1 | 0.5 | 79.6 | 72.5 | 86.2 | 0.0 |
| Qwen3 30B A3B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 95.0 | 90.8 | 98.3 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 95.0 | 90.8 | 98.3 | 0.0 |
| Qwen3 30B A3B | role | 0.0 | 0.0 | 0.0 | 15 | 1.7 | 0.0 | 4.2 | 15 | 65.8 | 58.3 | 73.3 | 15 | 1.7 | 0.0 | 4.2 | 0.5 | 64.2 | 55.8 | 71.7 | 0.0 |
| Llama 3.3 70B | both | 0.4 | 0.0 | 1.2 | 30 | 0.0 | 0.0 | 0.0 | 30 | 91.7 | 87.9 | 95.4 | 30 | -0.4 | -1.2 | 0.0 | 1.0 | 91.7 | 87.5 | 95.4 | 0.0 |
| Llama 3.3 70B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 98.3 | 95.8 | 100.0 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 98.3 | 95.8 | 100.0 | 0.0 |
| Llama 3.3 70B | role | 0.8 | 0.0 | 2.5 | 15 | 0.0 | 0.0 | 0.0 | 15 | 85.0 | 79.2 | 90.8 | 15 | -0.8 | -2.5 | 0.0 | 1.0 | 85.0 | 79.2 | 90.8 | 0.0 |
| Qwen3 Next 80B | both | 0.0 | 0.0 | 0.0 | 30 | 0.0 | 0.0 | 0.0 | 30 | 89.6 | 85.4 | 93.3 | 30 | 0.0 | 0.0 | 0.0 | 1.0 | 89.6 | 85.4 | 93.3 | 0.0 |
| Qwen3 Next 80B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 95.0 | 90.8 | 98.3 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 95.0 | 90.8 | 98.3 | 0.0 |
| Qwen3 Next 80B | role | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 84.2 | 77.5 | 90.0 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 84.2 | 77.5 | 90.8 | 0.0 |
| GLM 4.5 Air 106B | both | 0.4 | 0.0 | 1.2 | 30 | 0.4 | 0.0 | 1.2 | 30 | 95.0 | 90.8 | 98.3 | 30 | 0.0 | -1.2 | 1.2 | 1.0 | 94.6 | 90.4 | 97.9 | 0.0 |
| GLM 4.5 Air 106B | name | 0.0 | 0.0 | 0.0 | 15 | 0.0 | 0.0 | 0.0 | 15 | 99.2 | 97.5 | 100.0 | 15 | 0.0 | 0.0 | 0.0 | 1.0 | 99.2 | 97.5 | 100.0 | 0.0 |
| GLM 4.5 Air 106B | role | 0.8 | 0.0 | 2.5 | 15 | 0.8 | 0.0 | 2.5 | 15 | 90.8 | 84.2 | 95.9 | 15 | 0.0 | -2.5 | 2.5 | 1.0 | 90.0 | 83.3 | 95.8 | 0.0 |
