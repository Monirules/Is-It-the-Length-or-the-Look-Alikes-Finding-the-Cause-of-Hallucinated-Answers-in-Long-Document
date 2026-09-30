# Timing test: qwen3_4b on NVIDIA GeForce RTX 5070 (pc)

Model load: 42 s. Prompt: normal. vLLM 0.30.0.

| length | documents | first question (reads document) | other 11 (cached) | per document | cached tokens per later question |
|---|---|---|---|---|---|
| 8K | 3 | 3.1 s | 2.1 s | 5.1 s | 9,739 of 9,767 |
| 32K | 3 | 16.6 s | 3.1 s | 19.7 s | 38,743 of 38,771 |

Fit: seconds per document = b*L + c*L^2 (L in K tokens), b = 0.6173, c = 0.000000

## Projected GPU time for the whole plan (this model, this GPU)

| experiment | hours | of which extrapolated (64K/128K) |
|---|---|---|
| exp2: Look-alike ladder at fixed length | 0.66 | 0.00 |
| exp2 repeats: 3 repeats at T=0.7 | 1.98 | 0.00 |
| exp3: Length with and without a strong look-alike, two filler types | 3.18 | 2.63 |
| exp4: One, two, four or eight copies of the same look-alike | 0.44 | 0.00 |
| exp5: Sibling padding against standard fixes at equal cost | 0.31 | 0.00 |
| exp6: Natural Questions with the gold passage removed | 3.82 | 0.00 |
| exp7: Does asking 12 questions in one call hide made-up answers? | 0.20 | 0.00 |
| **total** | **10.59** | 2.63 |

Extrapolated rows use lengths this GPU could not run; re-run timing_test.py on the cluster for them.
