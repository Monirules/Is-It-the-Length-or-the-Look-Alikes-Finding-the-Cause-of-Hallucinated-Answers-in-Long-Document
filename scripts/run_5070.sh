#!/usr/bin/env bash
# scripts/run_5070.sh
#
# Step 6: the first end-to-end test on the RTX 5070 PC.
#   Qwen3 4B Instruct 2507, 20 documents at 32K from Exp 2 (spread over every ladder x level cell),
#   one question per call, normal prompt, temperature 0.
#
# NOTE on "4 bit": the plan said a 4-bit version, but vLLM (0.11+) removed bitsandbytes 4-bit. We use
# FP8 (8-bit), which the RTX 5070 runs natively; it is closer to the full model, which is better.
# As planned, no paper number comes from the PC.
#
# What it runs, in order:
#   1. checks (conda env, GPU, profile)
#   2. makes sure the Exp 2 and Exp 3 documents exist (reuses them if already built)
#   3. timing test: one test cell at 8K and 32K -> outputs/timing/  (skip with --skip-timing)
#   4. the 20-document run -> answers in ~/nullscale_work/outputs/answers/exp2/qwen3_4b/
#   5. first look (provisional) -> outputs/first_run/, then official scoring -> outputs/results/
# Everything is also logged to logs/run_5070_<time>.txt.
#
# Run from the project folder, in Ubuntu (WSL), inside the nullscale env:
#   bash scripts/run_5070.sh                 # everything (~10-20 minutes)
#   bash scripts/run_5070.sh --skip-timing   # skip step 3
#   bash scripts/run_5070.sh --n-docs 4      # a quicker try
set -euo pipefail

MODEL="qwen3_4b"
EXP="exp2"
N_DOCS=20
SKIP_TIMING=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-timing) SKIP_TIMING=1 ;;
    --n-docs) N_DOCS="$2"; shift ;;
    --model) MODEL="$2"; shift ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac
  shift
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs
LOG="logs/run_5070_$(date +%Y%m%d_%H%M%S).txt"
exec > >(tee -a "$LOG") 2>&1
step() { echo; echo "================ $* ================"; }

step "1/5 Checks"
if [[ "${CONDA_DEFAULT_ENV:-}" != "nullscale" ]]; then
  echo "Please run:  conda activate nullscale   (then run this script again)"; exit 1
fi
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader || { echo "GPU not visible"; exit 1; }
PROFILE="$(python -c 'from nullscale.config import load_paths; print(load_paths()["profile"])')"
echo "profile: $PROFILE   model: $MODEL   documents: $N_DOCS"
[[ "$PROFILE" == "pc" ]] || echo "WARNING: this script is meant for the PC profile"

step "2/5 Dataset (reuses documents that already exist)"
python -m nullscale.build_dataset --exp exp2,exp3

if [[ "$SKIP_TIMING" == "0" ]]; then
  step "3/5 Timing test: one test cell at 8K and 32K"
  python -m run.timing_test --model "$MODEL" --lengths 8,32 --n-docs 3
else
  step "3/5 Timing test skipped"
fi

step "4/5 Answer $N_DOCS documents at 32K, one question per call"
python -m run.run_vllm --model "$MODEL" --exp "$EXP" --n-docs "$N_DOCS" --balanced --lengths 32 --prompt normal

step "5/5 Scoring: provisional first look, then the official rules (score/score_all.py)"
python scripts/first_look.py --model "$MODEL" --exp "$EXP"
python -m score.score_all --exp "$EXP" --model "$MODEL"

step "Done"
echo "Log:      $LOG"
echo "Figures:  $PROJECT_ROOT/outputs/first_run/  and  $PROJECT_ROOT/outputs/timing/"
echo "Official: $PROJECT_ROOT/outputs/results/results_table.md"
echo "Answers:  $(python -m nullscale.config --get outputs.answers)/$EXP/$MODEL/"
