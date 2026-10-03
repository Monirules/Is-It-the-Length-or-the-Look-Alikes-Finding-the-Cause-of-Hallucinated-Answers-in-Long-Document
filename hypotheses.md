# Hypotheses and expected results (pre-registered)

**Project:** Is It the Length or the Look-Alikes? Finding the Cause of Hallucinated Answers in Long Document Question Answering (NAACL 2027)
**Authors:** M. I. Mahmud and Jayden, under Prof. Justin Zhan
**Fixed on:** 3 October 2026, before any main run (the only model answers so far are the Step 6 PC test: Qwen3 4B, 240 answers, which is not a paper result).
**Copied from:** Project Proposal, Sections 2, 5, 9 and 10.
**Review:** Monirul reviews and signs below. After sign-off, this file is not edited. Any later change goes in a dated note at the end, with the reason.

## Core idea

To give an answer, a model needs only **one** record that matches. To say "not found", it must **reject every record** in the document. So **one convincing look-alike record may be enough** to cause a made-up answer, whatever the length.

## Research questions

| | Question | Experiment | Test |
|---|---|---|---|
| **RQ1** | When length is fixed, do stronger look-alike records cause more made-up answers? | Exp 2 (ladder none / weak / medium / strong at 32K); Exp 4 (1, 2, 4, 8 copies) | made-up rate rises with level; logistic regression, level as an ordered predictor |
| **RQ2** | When look-alike records are fixed, does length alone cause more made-up answers? | Exp 3 (8K, 32K, 64K, 128K; with and without a strong look-alike; two filler types) | coefficient of log2(length) with the look-alike held fixed |
| **RQ3** | Does Roig's released data show the same pattern when trap questions are split by whether a look-alike was present? | Exp 1 (RIKER2, no model runs) | made-up rate, look-alike present vs. none, at 32K, 128K, 200K |
| **RQ4** | Does filling the context with records of the same kind that clearly lack the asked fact (sibling padding) reduce made-up answers, and is it cheaper than standard fixes? | Exp 5 (sibling padding vs. strict prompt, fact checker, reranker) | made-up rate and answer accuracy at equal cost |

Supporting checks: Exp 6 (real text: Natural Questions with the gold passage removed) and Exp 7 (12 questions in one call).

## Expected results and what each would mean

We fixed the meaning of every result before running, so the paper has a clear message in each case.

| Result | Message of the paper |
|---|---|
| Look-alikes matter, length does not | Control **what** goes into the context, not only **how much** |
| Both matter | Two separate causes. We report the length at which length starts to matter for each model |
| Length matters, look-alikes do not | First controlled proof of Roig's length effect. Shorter or chunked contexts are the fix |
| Neither matters up to 128K | The cause lies elsewhere. Exp 7 on question batching becomes the main result |

## Directional predictions (follow from the core idea; Monirul to confirm or strike before sign-off)

1. **RQ1:** made-up answers rise from none to strong look-alikes; strong is clearly above none for every model family. Most made-up answers copy the look-alike's value (high capture rate).
2. **RQ2:** with the look-alike held fixed, the effect of length is much smaller than the effect of one strong look-alike (exchange rate above 1 doubling).
3. **RQ3:** in RIKER2, part of the length effect is explained by look-alike presence.
4. **RQ4:** sibling padding lowers made-up answers without lowering accuracy on questions that do have an answer.

## How results are measured (fixed)

| Metric | Meaning |
|---|---|
| Made-up answer rate | Share of no-answer questions where the model gives a specific answer (main result) |
| Correct refusal rate | Share of no-answer questions where the model says not found |
| Look-alike capture rate | Share of made-up answers that copy the look-alike record's value |
| Answer accuracy | Share of answerable questions answered correctly |
| Wrong refusal rate | Share of answerable questions where the model says not found |
| Exchange rate | Doublings of length that equal the effect of one strong look-alike |
| Scorer agreement | Agreement between our scoring rules and two human checkers on 300 answers |

- Scoring uses fixed written rules (`score/`), never an AI judge. A hedged guess counts as made up ("It is not listed, but maybe $5,000").
- Every rate has a 95% confidence interval. A logistic regression separates the look-alike effect from the length effect, with its own baseline per model and question type. P-values of the main tests are corrected for multiple comparisons.
- Every question is sent in its own call, at temperature 0. Exp 2 is repeated three times at temperature 0.7.
- All paper numbers come from the cluster (full-precision or FP8 weights), not from the PC.

## Sign-off

- Written by: Jayden's part, prepared by M. I. Mahmud on 3 October 2026 (Jayden was ill)
- Reviewed by Monirul: ______________________  Date: __________
- Seen by Jayden: ______________________  Date: __________

## Change log

(none)
