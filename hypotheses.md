# Hypotheses and Results

**Project:** Is It the Length or the Look-Alikes? Finding the Cause of Hallucinated Answers in Long Document Question Answering (NAACL 2027)
**Date:** October 6, 2026

## Core Idea
To give an answer, a model needs only **one** record that matches. To say "not found", it must **reject every record** in the document. Our premise was that **one convincing look-alike record may be enough** to cause a made-up answer, regardless of the context length.

## Research Questions & Final Outcomes

| RQ | Question | Final Outcome & Evidence |
| :--- | :--- | :--- |
| **RQ1** | When length is fixed, do stronger look-alike records cause more made-up answers? | **Supported.** A strong look-alike adds 64 to 94 points to the made-up answer rate across all 7 tested models. |
| **RQ2** | When look-alike records are fixed, does length alone cause more made-up answers? | **Supported (with nuance).** Length matters, but primarily past a model's reading limit. The regression exchange rate is 5.9 doublings (95% interval 5.6 to 6.3), meaning one strong look-alike equals a document 58 times longer. Length alone showed a large effect only in Gemma 3 27B, Llama 3.3 70B, and GLM 4.5 Air—and specifically at lengths where their overall answer accuracy had already dropped. |
| **RQ3** | Does Roig's released data show the same pattern when trap questions are split by whether a look-alike was present? | **Not supported.** In the RIKER2 dataset, the look-alike share is flat (63%, 62%, and 61% across 32K, 128K, and 200K lengths). Look-alikes cannot explain Roig's length curve; his curve represents genuine length damage. Our contribution proves a *second*, separate cause that his design could not isolate. |
| **RQ4** | Does filling the context with records of the same kind that clearly lack the asked fact (sibling padding) reduce made-up answers, and is it cheaper than standard fixes? | **Partly supported.** Sibling filler does lower made-up answers, but it also drops answer accuracy by 1.7 to 24.1 points. It does not hold up as a viable fix. |

## Overall Conclusion: Both Matter
The data firmly supports a dual-cause paradigm for hallucinations in long-context QA:
1. **Look-alikes** cause a massive jump in made-up answers at *every* length and in *every* model. 
2. **Length** adds made-up answers only past a specific "breaking point" that differs by model. This breaking point perfectly aligns with the point where the model stops reading well overall. 

## Supporting Checks & Exploratory Findings
* **Question Batching (Exp 7):** Asking 12 questions in one call actually *increased* made-up answers. For example, Qwen3 4B rose from 63.1% to 75.6%, and Llama 3.1 8B rose from 57.5% to 95.0%. 
* **Real Text (Exp 6):** Tested against Natural Questions with the gold passage removed to ensure findings generalize beyond synthetic data.
* **Strict Prompt Baseline:** A strict-prompt run on the Exp 2 documents with a strong look-alike was added as a baseline to compare against the sibling filler fix.

## Final Measurement Methodology

| Metric | Meaning |
| :--- | :--- |
| **Made-up answer rate** | Share of no-answer questions where the model gives a specific answer (main result). |
| **Correct refusal rate** | Share of no-answer questions where the model says not found. |
| **Look-alike capture rate** | Share of made-up answers that copy the look-alike record's value. |
| **Answer accuracy** | Share of answerable questions answered correctly. |
| **Exchange rate** | Doublings of length that equal the effect of one strong look-alike (Calculated at 5.9). |
| **Scorer agreement** | Automated rule agreement against RIKER2's official scorer yielded 99.21% agreement (Cohen's kappa 0.981) across 605,948 answers, replacing the need for manual hand-checks. |

*Note on Execution:* All scoring used fixed written rules. All model generation utilized the cluster (H200 FP8 weights). Gemma 3 27B was excluded from 128K runs due to context window limits, and GLM-4.5-Air capacities were adjusted accordingly for Exp 3.


