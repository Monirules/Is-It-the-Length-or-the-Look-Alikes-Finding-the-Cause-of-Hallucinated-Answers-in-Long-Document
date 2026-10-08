# What is inside RIKER2

Folder: `~/nullscale_work/data/riker2`. Made by riker/inspect_riker.py.

## Answer to the main question

**Yes: the full document text is included.** For every length, the file `<length>K_riker_<date>_concatenated.md` is the exact text the models read, with every lease, field report and HR report in it. The `.db` file is the ground truth and the `.yaml` file the questions. So we can search the documents themselves for look-alike records (riker/find_lookalikes.py).

## 32K context

**Documents** (`32K_riker_2025-12-12_195725_concatenated.md`): 114,060 characters, about 28,515 tokens (4 characters per token), 110 documents: 10 leases, 44 field reports, 56 hr reports.

**Ground truth** (`32K_riker_2025-12-12_195725.db`): pool_lessees 1000, pool_lessors 50, pool_agents 15, pool_guarantors 200, pool_managers 5, lease_documents 10, composition_metadata 97, sqlite_sequence 1, field_reports 44, employee_manager_assignments 65, hr_reports 56.
Database records found as documents in the text: 110 of 110.

**Test set** (`32K_riker_2025-12-12_195725.yaml`): 371 questions.

| document type | L01 | L02 | L03 | L04 | L05 | L06 | L07 | L08 | L09 | L10 | L11 | L12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| field_report | 8 | 8 | 7 | 7 | 5 | 5 | 5 | 4 | 4 | 5 | 15 | 15 |
| hr | 8 | 8 | 7 | 7 | 5 | 5 | 5 | 5 | 4 | 4 | 15 | 15 |
| lease_document | 17 | 17 | 16 | 16 | 11 | 11 | 11 | 10 | 9 | 11 | 33 | 33 |

Trap questions (L11 + L12): 126; expected answers: {'Unknown': 38, 'N/A': 85, 'NONE': 3}.

Examples:

- `lease_document_L11_T11_0001`: What is the monthly rent for Adomas Forberg's lease with Willmer Bienko starting 2024-09-25? -> expected **N/A**
- `field_report_L11_T15_0001`: Does Adelore Wurgler's field report about Diani Kosofsky on 2024-08-28 include property condition notes? -> expected **Unknown**
- `hr_L11_T01_0001`: When was Kylor Hesla's evaluation for June 2025 conducted? -> expected **N/A**
- `lease_document_L12_T31_0001`: What is the pet deposit for Drilon Friermood's lease with Willmer Bienko starting 2024-09-25? -> expected **N/A**
- `field_report_L12_T15_0001`: Who is the manager that commented on Kylor Rauseo's field report about Tessalee Kilcoin on 2025-04-08? -> expected **NONE**
- `hr_L12_T03_0001`: What is written under "Manager Comments:" in Chela Woerth's evaluation for December 2024? -> expected **N/A**

## 128K context

**Documents** (`128K_riker_2025-12-12_211037_concatenated.md`): 408,998 characters, about 102,250 tokens (4 characters per token), 369 documents: 37 leases, 216 field reports, 116 hr reports.

**Ground truth** (`128K_riker_2025-12-12_211037.db`): pool_lessees 1000, pool_lessors 20, pool_agents 15, pool_guarantors 200, pool_managers 5, lease_documents 37, composition_metadata 367, sqlite_sequence 1, field_reports 216, employee_manager_assignments 35, hr_reports 116.
Database records found as documents in the text: 369 of 369.

**Test set** (`128K_riker_2025-12-12_211037.yaml`): 538 questions.

| document type | L01 | L02 | L03 | L04 | L05 | L06 | L07 | L08 | L09 | L10 | L11 | L12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| field_report | 10 | 10 | 10 | 10 | 7 | 7 | 7 | 7 | 6 | 6 | 20 | 20 |
| hr | 10 | 10 | 10 | 10 | 7 | 7 | 7 | 7 | 6 | 4 | 20 | 20 |
| lease_document | 25 | 25 | 25 | 25 | 17 | 17 | 17 | 17 | 16 | 16 | 50 | 50 |

Trap questions (L11 + L12): 180; expected answers: {'Unknown': 55, 'N/A': 120, 'NONE': 5}.

Examples:

- `lease_document_L11_T11_0001`: What is the monthly rent for Seraiah Walsch's lease with Laini Philen starting 2020-09-18? -> expected **N/A**
- `field_report_L11_T15_0001`: Does Dorce Switaj's field report about Ofir Dilkes on 2024-03-28 mention a competitor property? -> expected **Unknown**
- `hr_L11_T01_0001`: What is the performance rating in Lisbed Riesland's evaluation for December 2024? -> expected **N/A**
- `lease_document_L12_T31_0001`: What is the pet deposit for Desiah Roisman's lease with Laini Philen starting 2020-01-13? -> expected **N/A**
- `field_report_L12_T15_0001`: What are the manager's comments in Lisbed Pfile's field report about Shaunt Desalvo on 2025-06-15? -> expected **N/A**
- `hr_L12_T03_0001`: What is written under "Manager Comments:" in Sausha Heronemus's evaluation for June 2024? -> expected **N/A**

## 200K context

**Documents** (`200K_riker_2025-12-12_204529_concatenated.md`): 723,860 characters, about 180,965 tokens (4 characters per token), 637 documents: 60 leases, 381 field reports, 196 hr reports.

**Ground truth** (`200K_riker_2025-12-12_204529.db`): pool_lessees 1000, pool_lessors 50, pool_agents 15, pool_guarantors 200, pool_managers 5, lease_documents 60, composition_metadata 596, sqlite_sequence 1, field_reports 381, employee_manager_assignments 65, hr_reports 196.
Database records found as documents in the text: 637 of 637.

**Test set** (`200K_riker_2025-12-12_204529.yaml`): 695 questions.

| document type | L01 | L02 | L03 | L04 | L05 | L06 | L07 | L08 | L09 | L10 | L11 | L12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| field_report | 13 | 13 | 12 | 12 | 9 | 9 | 8 | 8 | 8 | 8 | 25 | 25 |
| hr | 13 | 13 | 12 | 12 | 9 | 9 | 8 | 8 | 8 | 4 | 25 | 25 |
| lease_document | 34 | 33 | 33 | 33 | 23 | 22 | 22 | 22 | 22 | 22 | 66 | 67 |

Trap questions (L11 + L12): 233; expected answers: {'N/A': 160, 'Unknown': 65, 'NONE': 8}.

Examples:

- `lease_document_L11_T11_0001`: What is the monthly rent for Zabdiel Genaw's lease with Gurjit Holterman starting 2021-01-10? -> expected **N/A**
- `field_report_L11_T15_0001`: What property is discussed in Hafez Gavis's field report about Jashun Billetdeaux on 2020-08-26? -> expected **N/A**
- `hr_L11_T01_0001`: When was Tavonte Kissner's evaluation for December 2024 conducted? -> expected **N/A**
- `lease_document_L12_T31_0001`: What is the pet deposit for Timon Huyna's lease with Carville Caum starting 2025-05-20? -> expected **N/A**
- `field_report_L12_T15_0001`: What are the manager's comments in Breydan Tuszynski's field report about Shymel Dolcimascolo on 2025-09-22? -> expected **N/A**
- `hr_L12_T03_0001`: What is written under "Manager Comments:" in Doel Gawlas's evaluation for December 2024? -> expected **N/A**

## Model answers (RIKER2_March2026.zip)

1,800,599 answers from 3,696 runs of 35 models.

| context | runs | answers | failed replies (empty or error) | question ids not in the test set |
|---|---|---|---|---|
| 32K | 1,719 | 637,749 | 142,907 | 0 |
| 128K | 1,345 | 723,610 | 239,937 | 0 |
| 200K | 632 | 439,240 | 180,760 | 0 |

Models: `deepseek_v3`, `deepseek_v3_1`, `glm_4_5`, `glm_4_5_air`, `glm_4_6`, `glm_4_7`, `granite_4_0_h_micro`, `granite_4_0_h_small`, `granite_4_0_h_tiny`, `llama_3_1_405b_instruct`, `llama_3_1_70b_instruct`, `llama_3_1_8b_instruct`, `llama_3_2_1b_instruct`, `llama_3_2_3b_instruct`, `llama_3_3_70b_instruct`, `llama_4_maverick_17b_128e_instruct`, `llama_4_scout_17b_16e_instruct`, `minimax_m2`, `minimax_m2_1`, `qwen2_5_14b_instruct`, `qwen2_5_32b_instruct`, `qwen2_5_72b_instruct`, `qwen2_5_coder_14b_instruct`, `qwen2_5_coder_7b_instruct`, `qwen3_14b`, `qwen3_235b_a22b_instruct_2507`, `qwen3_235b_a22b_instruct_2507_fp8`, `qwen3_30b_a3b_instruct_2507`, `qwen3_32b`, `qwen3_4b`, `qwen3_4b_instruct_2507`, `qwen3_8b`, `qwen3_coder_30b_a3b_instruct`, `qwen3_coder_480b_a35b_instruct`, `qwen3_next_80b_a3b_instruct`

Temperatures: 0.0 (835 runs), 0.4 (840 runs), 0.7 (854 runs), 1.0 (1167 runs)
Hardware/platform folders: gaudi3_s1 (231), h200_s1 (627), h200_s2 (800), mi300x_s1 (648), mi300x_s2 (469), mi300x_s3 (480), mi300x_s4 (441)
Run status: ok 3696

## Roig's summary tables

- `128k_best_temp_aggregation.csv` (37 rows): hardware, model, best_temp, runs, aggregation, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `128k_best_temp_fabrication.csv` (37 rows): hardware, model, best_temp, runs, fabrication, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `128k_best_temp_grounding.csv` (37 rows): hardware, model, best_temp, runs, grounding, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `128k_best_temp_overall_acc.csv` (37 rows): hardware, model, best_temp, runs, overall_acc, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `128k_best_temp_truncation.csv` (37 rows): hardware, model, best_temp, truncation_pct, spread_pct, temps_tested, note, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct ...
- `128k_fabrication_by_temp.csv` (37 rows): hardware, model, fab_0_0, runs_0_0, fab_0_4, runs_0_4, fab_0_7, runs_0_7, fab_1_0, runs_1_0, total_runs, spread ...
- `128k_grounding_by_temp.csv` (37 rows): hardware, model, ground_0_0, runs_0_0, ground_0_4, runs_0_4, ground_0_7, runs_0_7, ground_1_0, runs_1_0, total_runs, spread ...
- `128k_summary.csv` (169 rows): platform, temperature, model, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct
- `128k_truncation_by_temp.csv` (37 rows): hardware, model, trunc_0_0, runs_0_0, trunc_0_4, runs_0_4, trunc_0_7, runs_0_7, trunc_1_0, runs_1_0, total_runs, spread ...
- `128k_variance_analysis.csv` (104 rows): context_size, model, hardware, temperature, mean, stdev, range, n_runs, between_temp_spread
- `128k_variance_analysis_by_metric.csv` (520 rows): context_size, model, hardware, metric, temperature, mean, stdev, range, n_runs, between_temp_spread
- `200k_best_temp_aggregation.csv` (16 rows): hardware, model, best_temp, runs, aggregation, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `200k_best_temp_fabrication.csv` (16 rows): hardware, model, best_temp, runs, fabrication, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `200k_best_temp_grounding.csv` (16 rows): hardware, model, best_temp, runs, grounding, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `200k_best_temp_overall_acc.csv` (16 rows): hardware, model, best_temp, runs, overall_acc, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `200k_best_temp_truncation.csv` (16 rows): hardware, model, best_temp, truncation_pct, spread_pct, temps_tested, note, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct ...
- `200k_fabrication_by_temp.csv` (16 rows): hardware, model, fab_0_0, runs_0_0, fab_0_4, runs_0_4, fab_0_7, runs_0_7, fab_1_0, runs_1_0, total_runs, spread ...
- `200k_grounding_by_temp.csv` (16 rows): hardware, model, ground_0_0, runs_0_0, ground_0_4, runs_0_4, ground_0_7, runs_0_7, ground_1_0, runs_1_0, total_runs, spread ...
- `200k_summary.csv` (79 rows): platform, temperature, model, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct
- `200k_truncation_by_temp.csv` (16 rows): hardware, model, trunc_0_0, runs_0_0, trunc_0_4, runs_0_4, trunc_0_7, runs_0_7, trunc_1_0, runs_1_0, total_runs, spread ...
- `200k_variance_analysis.csv` (44 rows): context_size, model, hardware, temperature, mean, stdev, range, n_runs, between_temp_spread
- `200k_variance_analysis_by_metric.csv` (220 rows): context_size, model, hardware, metric, temperature, mean, stdev, range, n_runs, between_temp_spread
- `32k_best_temp_aggregation.csv` (46 rows): hardware, model, best_temp, runs, aggregation, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `32k_best_temp_fabrication.csv` (46 rows): hardware, model, best_temp, runs, fabrication, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `32k_best_temp_grounding.csv` (46 rows): hardware, model, best_temp, runs, grounding, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `32k_best_temp_overall_acc.csv` (46 rows): hardware, model, best_temp, runs, overall_acc, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct, source_platform
- `32k_best_temp_truncation.csv` (46 rows): hardware, model, best_temp, truncation_pct, spread_pct, temps_tested, note, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct ...
- `32k_fabrication_by_temp.csv` (46 rows): hardware, model, fab_0_0, runs_0_0, fab_0_4, runs_0_4, fab_0_7, runs_0_7, fab_1_0, runs_1_0, total_runs, spread ...
- `32k_grounding_by_temp.csv` (46 rows): hardware, model, ground_0_0, runs_0_0, ground_0_4, runs_0_4, ground_0_7, runs_0_7, ground_1_0, runs_1_0, total_runs, spread ...
- `32k_summary.csv` (217 rows): platform, temperature, model, runs, overall_pct, faithfulness_pct, grounding_pct, fabrication_pct, aggregation_pct, truncation_pct
- `32k_truncation_by_temp.csv` (46 rows): hardware, model, trunc_0_0, runs_0_0, trunc_0_4, runs_0_4, trunc_0_7, runs_0_7, trunc_1_0, runs_1_0, total_runs, spread ...
- `32k_variance_analysis.csv` (140 rows): context_size, model, hardware, temperature, mean, stdev, range, n_runs, between_temp_spread
- `32k_variance_analysis_by_metric.csv` (690 rows): context_size, model, hardware, metric, temperature, mean, stdev, range, n_runs, between_temp_spread
- `analysis.csv` (3696 rows): platform, test_type, temperature, context_size, experiment, model_name, run_number, timestamp, total_questions, correct_answers, overall_accuracy, single_doc_correct ...
- `failed_h200_s2_tokens.csv` (32 rows): group, model, run, timestamp, questions, input_tokens, output_tokens, total_tokens, truncated_count, truncated_output_tokens
- `fidelity.csv` (465 rows): platform, temperature, context, model, runs, faithfulness_accuracy_mean, faithfulness_accuracy_std, faithfulness_accuracy_cv, grounding_accuracy_mean, grounding_accuracy_std, grounding_accuracy_cv, fabrication_hall_rate_mean ...
- `incoherence.csv` (1499 rows): platform, temperature, context_size, model_name, category, truncated, total, truncation_rate, avg_total_tokens, avg_completion_tokens
- `model_summary.csv` (465 rows): platform, temperature, context_size, experiment, model_name, run_count, overall_mean, overall_std, overall_median, overall_min, overall_max, overall_cv ...
- `temperature_preference_analysis.csv` (90 rows): context_size, model, hardware, temp_0_0_mean, temp_0_0_sd, temp_0_0_n, best_temp, best_temp_mean, best_temp_sd, best_temp_n, diff_from_t0, max_sd ...
- `temperature_preference_by_metric.csv` (450 rows): metric, context_size, model, hardware, temp_0_0_mean, temp_0_4_mean, temp_0_7_mean, temp_1_0_mean, best_temp, best_temp_mean, diff_vs_t0, total_spread ...
- `tokens.csv` (4264 rows): platform, test_type, temperature, context_size, experiment, model, run, timestamp, questions, input_tokens, output_tokens, total_tokens ...
- `truncation_by_context_and_temperature.csv` (79 rows): context_size, model, hardware, temp_0_0_trunc_rate, temp_0_0_sd, temp_0_0_n, temp_0_4_trunc_rate, temp_0_4_sd, temp_0_4_n, temp_0_7_trunc_rate, temp_0_7_sd, temp_0_7_n ...
- `truncation_temperature_analysis.csv` (102 rows): context_size, model, hardware, temp_0_0_trunc, temp_0_4_trunc, temp_0_7_trunc, temp_1_0_trunc, best_temp, best_trunc_rate, worst_temp, worst_trunc_rate, spread ...

