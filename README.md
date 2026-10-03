# NullScale: Is It the Length or the Look-Alikes?

Code for the NAACL 2027 paper by **M. I. Mahmud** and **Jayden**, supervised by **Prof. Justin Zhan** (University of Cincinnati).

When a long document does not contain the answer, language models often make one up. Roig (2026) showed that this gets worse with document length. But longer documents also contain more records that **look like** the asked item. NullScale builds documents in which we control both things, and in which the answer is **proven absent**. This lets us tell which one causes the made-up answers.

## Folder layout

| Folder | What is in it | Owner |
|---|---|---|
| `configs/` | `paths.yaml` (PC and cluster folders), `models.yaml` (7 open models, 1 optional API model), `experiments.yaml` (Exp 1 to Exp 7) | Monirul |
| `nullscale/` | the document generator: fake world, records, look-alikes, filler, documents, questions, absence check | Monirul |
| `run/` | prompts, the vLLM runner, the timing test | Monirul |
| `score/` | official scoring rules: refusal, answer matching, look-alike capture, results table | Jayden |
| `riker/` | Exp 1: download, inspect and re-analyse Roig's RIKER2 data | Jayden |
| `tests/` | `test_absence.py` (generator), `test_scoring.py` (scoring rules) | both |
| `scripts/` | setup, the PC run (`run_5070.sh`), figures, first look | Monirul |
| `outputs/` | small results that go into git: figures, tables, reports | both |

Large files (model weights, documents, answers, RIKER2 data) live **outside** this folder, in the work folder from `configs/paths.yaml` (PC: `~/nullscale_work`). OneDrive and git never see them.

## Install (once)

All commands run in **Ubuntu (WSL)** on the PC, or on the cluster login node, from this project folder.

```bash
cd "/mnt/c/Users/mahmu/OneDrive/Desktop/Dr. Justin Zhan/One Record is Enough/nullscale-naacl2027"
bash scripts/setup_env.sh pc            # creates the conda env "nullscale" (Python 3.11, vLLM, PyTorch, ...)
conda activate nullscale
python -m nullscale.config --make-dirs  # checks the three config files and creates the work folders
huggingface-cli login                   # once; Llama and Gemma need their licence accepted on the website
```

On the cluster: `bash scripts/setup_env.sh cluster`, and fill in the `TODO` lines of `configs/paths.yaml` first.

## The agreed format of one saved answer

`run/run_vllm.py` writes **one JSON line per answer** to

```
<work folder>/outputs/answers/<exp>/<model>/<prompt>_t<temperature>_s<seed>.jsonl
```

with a `.meta.json` file next to it (settings, package versions, timings). Every line has exactly these fields. Both authors agreed on them; `score/` reads them.

| Field | Meaning |
|---|---|
| `run_id` | one id per run of `run_vllm.py` |
| `qid` | question id, `<doc_id>/<probe_id>` |
| `exp` | `exp2` ... `exp7` |
| `doc_id` | document id, e.g. `name-strong-c1-unrelated-32k-s22261057` |
| `probe_id` | `u0`-`u7` (no answer in the document) or `a0`-`a3` (has an answer) |
| `model`, `hf_id` | key in `configs/models.yaml`, and the Hugging Face name |
| `profile`, `quantization` | `pc` or `cluster`; e.g. `fp8 (PC)` or `bf16` |
| `prompt_style`, `prompt_version` | `normal`, `strict` or `batch12`; a hash of the prompt texts |
| `temperature`, `top_p`, `seed`, `max_tokens` | decoding settings |
| `question` | the question as asked |
| `answerable` | `true` if the answer is in the document |
| `field` | asked fact: `monthly_rent`, `deposit`, `start_date`, `end_date` or `floor` |
| `ladder`, `level`, `copies`, `filler`, `length_k` | the condition: `name`/`role`; `none`/`weak`/`medium`/`strong`; 1-8 copies; `unrelated`/`sibling`; 8, 32, 64 or 128 |
| `gold`, `gold_aliases` | the true answer and its other written forms (`null` and `[]` if there is no answer) |
| `lookalike_values` | the asked fact's value in the look-alike record(s), used for the capture tag |
| `response` | the model's full reply |
| `finish_reason`, `truncated` | `stop` or `length`; `truncated` is true when `max_tokens` was hit |
| `n_prompt_tokens`, `cached_prompt_tokens`, `n_output_tokens` | token counts; cached = reused document |
| `call_id`, `call_size`, `call_seconds`, `batch_index` | which vLLM call produced it, how many answers it held, its time; position inside a `batch12` reply |
| `timestamp`, `vllm_version` | when, and with which vLLM |
| `raw_batch_response` | `batch12` only: the whole numbered reply |

Scoring adds these fields (`score/score_all.py`, saved as `.scored.jsonl` in `<work folder>/outputs/scores/`):
`label` (correct / wrong_refusal / wrong / refused / made_up / other), `outcome` (correct / made_up / other), `captured`, `mentions_lookalike`, `source`, `refusal`, `hedged`, `answer_part`, `answer_source`, `scoring_version`.

## Running Steps 1 to 6

```bash
conda activate nullscale
python -m nullscale.config                          # Step 2: configs agree
python -m nullscale.build_dataset --exp all         # Steps 3-5: all documents and questions
python -m pytest tests/ -v                          # Step 5: absence proof + scoring rules
bash scripts/run_5070.sh                            # Step 6: Qwen3 4B, 20 documents at 32K, then scoring
python -m score.score_all                           # Step 6: official results table

python -m riker.download_riker                      # Step 2: RIKER2 (4.65 GB download)
python -m riker.inspect_riker                       # Step 2: what is inside
python -m riker.find_lookalikes                     # Step 3: mark every trap question
python -m riker.reanalyze_riker                     # Step 4: the Exp 1 chart
python -m score.refusal_rules --riker               # Step 5: refusal rules on RIKER2's answers
```

The research questions and the expected results are fixed in `hypotheses.md` **before** any main run.

## References

Roig, J. V. (2026). How Much Do LLMs Hallucinate in Document Q&A Scenarios? arXiv:2603.08274. Data: https://research.kamiwaza.ai/HowMuchDoLLMsHallucinateInDocQA/
