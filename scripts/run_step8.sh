#!/usr/bin/env bash
# scripts/run_step8.sh
#
# Step 8 cluster runs, using the existing runner (run/run_vllm.py) and scorer (score/score_all.py).
#   glm6     GLM-4.5-Air on Exp 6 (the only model missing there): 1,500 answers, 4 x H200, about 2-3 h
#   strict   optional baseline: strict prompt on the Exp 2 documents with a STRONG look-alike only,
#            all 7 models (or the ones you list), 360 answers per model, one small job per model
#   status   answers saved so far for both runs, and your queue
#   job      (internal) what one strict job runs on the GPU node
#
# Run on the cluster LOGIN node, from the project folder, inside the conda env:
#   conda activate nullscale
#   bash scripts/run_step8.sh glm6
#   bash scripts/run_step8.sh strict                       # all 7 models
#   bash scripts/run_step8.sh strict qwen3_4b,llama31_8b   # only these
#   bash scripts/run_step8.sh status
# Weights must be on disk (bash scripts/run_h200.sh check). Missing ones: bash scripts/run_h200.sh download <model>
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export NULLSCALE_PROFILE=cluster TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
ALL="qwen3_4b llama31_8b gemma3_27b qwen3_30b_a3b llama33_70b qwen3_next_80b glm45_air"

cfg() { python -m nullscale.config --profile cluster --get "$1" 2>/dev/null || true; }
mcfg() { python - "$1" "$2" <<'PY'
import sys
from nullscale.config import load_models
v = load_models()["open_models"][sys.argv[1]]
for k in sys.argv[2].split("."):
    v = v.get(k) if isinstance(v, dict) else None
print("" if v is None else v)
PY
}
need_env() { [[ "${CONDA_DEFAULT_ENV:-}" == "nullscale" ]] || { echo "Please run:  conda activate nullscale"; exit 1; }; }
model_dir() { local id; id="$(mcfg "$1" hf_id)"; echo "$(cfg hf_home)/hub/models--${id//\//--}"; }
count() { local n=0 f; for f in "$1" "${1%.jsonl}".part*of*.jsonl "$(dirname "$1")/parts/$(basename "${1%.jsonl}")".part*of*.jsonl; do
            [[ -f "$f" ]] && n=$(( n + $(wc -l < "$f") )); done; echo $n; }

cmd_glm6() {
  need_env
  local d; d="$(cfg data.nq)/exp6/questions.jsonl"
  [[ -f "$d" ]] || { echo "Exp 6 data not found at $d (copy it from the PC first)"; exit 1; }
  [[ -d "$(model_dir glm45_air)" ]] || { echo "GLM-4.5-Air weights missing: bash scripts/run_h200.sh download glm45_air"; exit 1; }
  bash scripts/run_h200.sh submit --models glm45_air --exps exp6 --no-repeats --hours 4
}

cmd_strict() {
  need_env
  local models="${1:-$ALL}"; models="${models//,/ }"
  local part acct qos logdir; part="$(cfg slurm.partition)"; acct="$(cfg slurm.account)"; qos="$(cfg slurm.qos)"
  logdir="$PROJECT_ROOT/logs/slurm"; mkdir -p "$logdir"
  for m in $models; do
    if [[ ! -d "$(model_dir "$m")" ]]; then echo "skip $m: weights missing (bash scripts/run_h200.sh download $m)"; continue; fi
    local tp; tp="$(mcfg "$m" cluster.tp_h200)"; tp="${tp:-1}"
    local big=$(( $(mcfg "$m" params_b) > 40 ? 128 : 32 ))
    local args=(--job-name="ns-strict-$m" --partition="$part" --gres="gpu:$tp" --nodes=1 --ntasks=1
                --cpus-per-task=$(( 8 * tp )) --mem="$(( 64 * tp + big ))G" --time="3:00:00" --output="$logdir/%x-%j.out")
    [[ -n "$acct" ]] && args+=(--account="$acct")
    [[ -n "$qos" ]] && args+=(--qos="$qos")
    args+=(--wrap="cd '$PROJECT_ROOT' && source \"\$(conda info --base)/etc/profile.d/conda.sh\" && conda activate nullscale && bash scripts/run_step8.sh job $m")
    echo "submitted $m: job $(sbatch --parsable "${args[@]}")  ($tp x H200, 3 h limit)"
  done
  echo "Watch: bash scripts/run_step8.sh status"
}

cmd_job() {   # on the GPU node
  local m="$1"
  need_env
  export HF_HOME="$(cfg hf_home)" NULLSCALE_GPU_TYPE=h200 HF_HUB_OFFLINE=1
  export VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_USE_DEEP_GEMM=0          # same settings as run_h200.sh job
  type module >/dev/null 2>&1 || source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
  module load gcc/11.3.0 2>/dev/null || true
  command -v nvcc >/dev/null 2>&1 || module load cuda 2>/dev/null || true
  command -v nvcc >/dev/null 2>&1 && export CUDA_HOME="${CUDA_HOME:-$(dirname "$(dirname "$(command -v nvcc)")")}"
  echo "== $(date '+%F %T') $m strict prompt, Exp 2 strong only, on $(hostname) =="
  nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true
  python -m run.run_vllm --model "$m" --exp exp2 --prompt strict --levels strong --profile cluster
  python -m score.score_all --exp exp2 --model "$m" --no-figures
  echo "== $(date '+%F %T') finished $m =="
}

cmd_status() {
  need_env
  local ans; ans="$(cfg outputs.answers)"
  printf "%-16s %-22s %-22s\n" model "exp6 (expect 1500)" "exp2 strict (expect 360)"
  for m in $ALL; do
    local e6="-"; [[ "$m" == glm45_air ]] && e6="$(count "$ans/exp6/$m/normal_t0_s0.jsonl")"
    printf "%-16s %-22s %-22s\n" "$m" "$e6" "$(count "$ans/exp2/$m/strict_t0_s0.jsonl")"
  done
  echo; squeue -u "$USER" -o "%.10i %.20j %.8T %.10M %.10l %.6b %R" 2>/dev/null || true
}

case "${1:-}" in
  glm6) cmd_glm6 ;;
  strict) shift; cmd_strict "${1:-}" ;;
  job) shift; cmd_job "$1" ;;
  status) cmd_status ;;
  *) sed -n '2,19p' "$0"; exit 1 ;;
esac
