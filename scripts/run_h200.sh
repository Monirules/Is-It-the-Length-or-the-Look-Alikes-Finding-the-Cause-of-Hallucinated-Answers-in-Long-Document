#!/usr/bin/env bash
# scripts/run_h200.sh  (owner: Monirul)
#
# Step 7: the main runs on the UC ARC cluster's H200 GPUs (partition gpu-h200, 8 x H200 141 GB).
# Exp 2, Exp 3 and Exp 4 for all 7 open models, smallest model first.
#
# How the GPUs are used (two kinds of parallel work)
#   * Several models at once: every model is its own Slurm job, so free H200s run different models together.
#   * Several GPUs for one model (data parallel): a job with G GPUs runs G / tp copies of the model, one per
#     GPU group (tp = GPUs one copy needs: 1 for most models, 2 for GLM-4.5-Air). Each copy answers every
#     (G/tp)-th document; run/merge_shards.py joins the parts afterwards. 2 GPUs = about 2x faster.
# Inside a job: exp2 (T=0) -> exp3 -> exp4 -> exp2 repeats (T=0.7, seeds 1-3) -> official scoring.
# Every run resumes where it stopped, so a job that hits its time limit is simply submitted again.
# Documents longer than a model's window are SKIPPED and listed (never cut): <answers>.skipped.json.
#
# Run on the cluster LOGIN node, from the project folder, inside the conda env:
#   conda activate nullscale
#   bash scripts/run_h200.sh check                         # 1. settings, GPUs, storage, data, models
#   bash scripts/run_h200.sh download [models]             # 2. model weights (login node has internet)
#   bash scripts/run_h200.sh build                         # 3. Exp 2/3/4 documents (same seeds = same documents as the PC)
#   bash scripts/run_h200.sh submit --dry-run              # 4a. show the sbatch commands and GPU-hours
#   bash scripts/run_h200.sh submit                        # 4b. one job per model, smallest first
#   bash scripts/run_h200.sh status                        # 5. answers saved vs expected, and the queue
#   bash scripts/run_h200.sh cleanup qwen3_4b              # free a finished model's weights (disk)
# Options for submit:
#   --models qwen3_4b,llama31_8b   only these models (default: all 7, smallest first)
#   --exps exp2,exp3,exp4,exp6     experiments (default exp2,exp3,exp4; exp6 needs data/nq/exp6 on the cluster)
#   --gpus N                       GPUs per job (default: 2 copies of the model = 2 GPUs, 4 for GLM-4.5-Air)
#   --hours H                      wall-time limit per job (default by model size, capped by max_hours_per_job)
#   --no-repeats                   skip the three T=0.7 repeats of Exp 2
#   --cleanup                      delete the model's weights when all its answers are saved (saves disk)
#   --chain                        each job starts after the previous one ends
# Inside an interactive GPU session (salloc -p gpu-h200 --gres=gpu:2 ...) you can run one model directly:
#   bash scripts/run_h200.sh job qwen3_4b exp2,exp3,exp4
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export NULLSCALE_PROFILE=cluster
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

ALL_MODELS="qwen3_4b llama31_8b gemma3_27b qwen3_30b_a3b llama33_70b qwen3_next_80b glm45_air"   # smallest first
EXPECTED_exp2=1440; EXPECTED_exp3=3840; EXPECTED_exp4=960; EXPECTED_exp6=1500

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
hfdl() {   # hfdl <repo> [all|tokenizer]   (Python API: works with every huggingface_hub version)
  python - "$1" "${2:-all}" <<'PY'
import sys
from huggingface_hub import snapshot_download
repo, what = sys.argv[1], sys.argv[2]
if what == "tokenizer":
    snapshot_download(repo, allow_patterns=["tokenizer*", "*.json", "*.model", "*.txt"])
else:
    snapshot_download(repo, ignore_patterns=["*.pth", "original/*", "*.gguf"], max_workers=8)
PY
}
need_env() {
  if [[ "${CONDA_DEFAULT_ENV:-}" != "nullscale" ]]; then
    echo "Please run:  conda activate nullscale   (then run this again)"; exit 1
  fi
}
gpu_type() { local g; g="$(cfg slurm.gpu_type)"; [[ -z "$g" || "$g" == TODO* ]] && echo "h200" || echo "$g"; }
tp_for() { local t; t="$(mcfg "$1" "cluster.tp_$(gpu_type)")"; [[ -z "$t" ]] && t="$(mcfg "$1" cluster.tp_h200)"; echo "${t:-1}"; }
model_dir() { local id; id="$(mcfg "$1" hf_id)"; echo "$(cfg hf_home)/hub/models--${id//\//--}"; }
hours_for() {   # wall time for ONE copy of the model doing everything; divided by the number of copies
  local p; p="$(mcfg "$1" params_b)"; local copies="$2"; local cap; cap="$(cfg slurm.max_hours_per_job)"
  local h=10; (( p > 10 )) && h=16; (( p > 40 )) && h=30
  h=$(( (h + copies - 1) / copies + 2 ))          # + 2 h for loading and the T=0.7 repeats' overhead
  (( h > ${cap:-24} )) && h=${cap:-24}; echo "$h"
}

# ----------------------------------------------------------------------------- check
cmd_check() {
  need_env
  echo "== settings (configs/paths.yaml, profile cluster) =="
  for k in work_root hf_home slurm.partition slurm.gpu_type slurm.account slurm.qos slurm.max_hours_per_job slurm.max_gpus_per_job; do
    printf "  %-24s %s\n" "$k" "$(cfg "$k")"
  done
  echo; echo "== H200 partition =="
  if command -v sinfo >/dev/null; then
    sinfo -p "$(cfg slurm.partition)" -o "  nodes %D | GPUs per node %G | time limit %l | state %T" || true
    echo "  your Slurm accounts and QOS:"
    sacctmgr -n show assoc user="$USER" format=Account%20,Partition%14,QOS%40 2>/dev/null | sed 's/^/   /' || true
  else
    echo "  sinfo not found: run this on the cluster login node"
  fi
  echo; echo "== storage (models need ~400 GB; data + answers ~30 GB) =="
  for d in "$(cfg work_root)" "$(cfg hf_home)" "/N/lustre/scratch/$USER" "/N/scratch/$USER" "/scratch/$USER" "$HOME"; do
    [[ -d "$d" ]] && printf "  %-55s free %s\n" "$d" "$(df -h --output=avail "$d" 2>/dev/null | tail -1 | tr -d ' ')"
  done
  command -v lfs >/dev/null && lfs quota -h -p proj-606 /N/lustre 2>/dev/null | sed 's/^/  /' || true
  echo "  If a scratch folder above has more room, set hf_home in configs/paths.yaml to it."
  echo; echo "== data =="
  local data; data="$(cfg data.nullscale)"
  for e in exp2 exp3 exp4; do
    n=0; [[ -f "$data/$e/questions.jsonl" ]] && n=$(wc -l < "$data/$e/questions.jsonl")
    printf "  %-5s %6s questions (expected %s)\n" "$e" "$n" "$(eval echo \$EXPECTED_$e)"
  done
  n=0; [[ -f "$(cfg data.nq)/exp6/questions.jsonl" ]] && n=$(wc -l < "$(cfg data.nq)/exp6/questions.jsonl")
  printf "  %-5s %6s questions (expected %s)\n" exp6 "$n" "$EXPECTED_exp6"
  echo; echo "== models =="
  for m in $ALL_MODELS; do
    d="$(model_dir "$m")"; s="not downloaded"
    [[ -d "$d/snapshots" ]] && s="$(du -shL "$d/snapshots" 2>/dev/null | cut -f1)"   # -L: files are links to a shared blob store
    printf "  %-16s %-46s tp=%s  %s\n" "$m" "$(mcfg "$m" hf_id)" "$(tp_for "$m")" "$s"
  done
  echo; echo "== 128K documents vs each model's window =="
  python - <<'PY'
from nullscale.config import load_models
for k, m in load_models()["open_models"].items():
    f = 1.21 if m["family"] in ("qwen", "gemma") else (1.04 if m["family"] == "glm" else 1.0)
    need = (128_000 * 1.01 + 1500 + 256) * f
    print(f"  {k:16s} window {m['max_model_len']:>7,}  needs ~{need:>9,.0f}  {'OK' if need <= m['max_model_len'] else '-> 128K documents SKIPPED'}")
PY
  echo; echo "Next: bash scripts/run_h200.sh download"
}

# ----------------------------------------------------------------------------- download / cleanup
download_one() {
  local m="$1"; local id base; id="$(mcfg "$m" hf_id)"; base="$(mcfg "$m" base_hf_id)"
  echo "== $m: $id =="
  hfdl "$id" all
  [[ "$base" != "$id" ]] && hfdl "$base" tokenizer || true
  echo "  done: $(du -shL "$(model_dir "$m")/snapshots" | cut -f1)"
}
cmd_download() {
  need_env
  export HF_HOME="$(cfg hf_home)"; mkdir -p "$HF_HOME"
  local models="${1:-$ALL_MODELS}"
  echo "Downloading to $HF_HOME  (free: $(df -h --output=avail "$HF_HOME" | tail -1 | tr -d ' '))"
  echo "Needs 'hf auth login' (or huggingface-cli login) with the Llama and Gemma licences accepted."
  hfdl meta-llama/Llama-3.1-8B-Instruct tokenizer   # reference tokenizer
  for m in ${models//,/ }; do download_one "$m"; done
  echo "Next: bash scripts/run_h200.sh build"
}
cmd_cleanup() {
  local m="$1"; local d; d="$(model_dir "$m")"
  [[ -d "$d" ]] || { echo "$m: no weights at $d"; return; }
  echo "deleting $m ($(du -shL "$d/snapshots" 2>/dev/null | cut -f1)), including its files in the shared blob store"
  python - "$d" <<'PY'
import os, shutil, sys
d = sys.argv[1]
for root, _, files in os.walk(os.path.join(d, "snapshots")):
    for f in files:
        target = os.path.realpath(os.path.join(root, f))
        if os.path.isfile(target):
            os.remove(target)
shutil.rmtree(d)
PY
}

# ----------------------------------------------------------------------------- build
cmd_build() {
  need_env
  export HF_HOME="$(cfg hf_home)"
  python -m nullscale.build_dataset --exp exp2,exp3,exp4 --workers "${SLURM_CPUS_ON_NODE:-8}"
  echo "Next: bash scripts/run_h200.sh submit --dry-run"
}

# ----------------------------------------------------------------------------- job (on the GPU node)
run_sharded() {   # run_sharded <model> <exp> <tp> <ncopies> <gpu groups...> -- <extra run_vllm args>
  local model="$1" exp="$2" tp="$3" n="$4"; shift 4
  local groups=(); while [[ "$1" != "--" ]]; do groups+=("$1"); shift; done; shift
  local extra=("$@") temp=0 seed=0 k
  for (( k = 0; k < ${#extra[@]}; k++ )); do
    [[ "${extra[$k]}" == "--temperature" ]] && temp="${extra[$((k+1))]}"
    [[ "${extra[$k]}" == "--seed" ]] && seed="${extra[$((k+1))]}"
  done
  local stem; stem="normal_t$(python -c "print(f'{float($temp):g}')")_s$seed"
  if (( n == 1 )); then
    CUDA_VISIBLE_DEVICES="${groups[0]}" python -m run.run_vllm --model "$model" --exp "$exp" --profile cluster "${extra[@]}"
    return
  fi
  local logdir="$PROJECT_ROOT/logs/slurm/${SLURM_JOB_ID:-local}-$model"; mkdir -p "$logdir"
  local pids=() logs=()
  for (( k = 0; k < n; k++ )); do
    local log="$logdir/$exp-$stem-part$k.log"
    CUDA_VISIBLE_DEVICES="${groups[$k]}" python -m run.run_vllm --model "$model" --exp "$exp" --profile cluster \
      "${extra[@]}" --shard "$k" --num-shards "$n" > "$log" 2>&1 &
    pids+=($!); logs+=("$log")
    echo "  copy $k on GPU(s) ${groups[$k]}  (log: ${log#$PROJECT_ROOT/})"
    sleep 20                                  # stagger start-up so the copies do not read the weights at the same instant
  done
  local fail=0
  for k in "${!pids[@]}"; do
    if wait "${pids[$k]}"; then tail -n 1 "${logs[$k]}" | sed "s/^/  copy $k: /"
    else fail=1; echo "  copy $k FAILED; last lines of ${logs[$k]#$PROJECT_ROOT/}:"; tail -n 15 "${logs[$k]}"; fi
  done
  python -m run.merge_shards --exp "$exp" --model "$model" --stem "$stem"
  return $fail
}

cmd_job() {
  local model="$1" exps="${2:-exp2,exp3,exp4}" repeats="${3:-1}" cleanup="${4:-0}"
  need_env
  export HF_HOME="$(cfg hf_home)"
  export NULLSCALE_GPU_TYPE="$(gpu_type)"
  # vLLM's FlashInfer parts compile small GPU programs on first use and need nvcc (the CUDA compiler),
  # which is not on the GPU nodes by default. 1) use PyTorch's own sampler instead of FlashInfer's;
  # 2) load the cluster's CUDA module so nvcc exists for anything else that needs it (MoE models).
  export VLLM_USE_FLASHINFER_SAMPLER=0
  # FP8 block-quantized models (Qwen3-Next-FP8, GLM-4.5-Air-FP8) would JIT-compile DeepGEMM kernels with
  # nvcc + a C++20 host compiler; the node's default gcc is too old. Use vLLM's prebuilt CUTLASS/Triton
  # FP8 kernels instead (same results), and load a newer gcc for any other JIT step.
  export VLLM_USE_DEEP_GEMM=0
  type module >/dev/null 2>&1 || source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
  module load gcc/11.3.0 2>/dev/null || true
  if ! command -v nvcc >/dev/null 2>&1; then
    module load cuda 2>/dev/null || true
  fi
  echo "gcc: $(gcc -dumpversion 2>/dev/null)  VLLM_USE_DEEP_GEMM=$VLLM_USE_DEEP_GEMM"
  if command -v nvcc >/dev/null 2>&1; then
    export CUDA_HOME="${CUDA_HOME:-$(dirname "$(dirname "$(command -v nvcc)")")}"
    echo "nvcc: $(command -v nvcc)  CUDA_HOME=$CUDA_HOME"
  else
    echo "WARNING: nvcc not found; FlashInfer sampler disabled, other FlashInfer kernels may fail"
  fi
  local tp; tp="$(tp_for "$model")"
  # GPUs given to this job
  local vis="${CUDA_VISIBLE_DEVICES:-}"
  [[ -z "$vis" ]] && vis="$(nvidia-smi --query-gpu=index --format=csv,noheader | paste -sd, -)"
  IFS=',' read -r -a gpus <<< "$vis"
  local n=$(( ${#gpus[@]} / tp )); (( n < 1 )) && { echo "need $tp GPU(s) for $model, got ${#gpus[@]}"; exit 1; }
  local groups=() k
  for (( k = 0; k < n; k++ )); do groups+=("$(IFS=,; echo "${gpus[*]:$((k * tp)):$tp}")"); done
  echo "== $(date '+%F %T')  $model on $(hostname): ${#gpus[@]} GPU(s) -> $n copies x tp $tp  (${groups[*]}) =="
  nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true

  # weights: download once here if they are not there yet, then work offline
  if [[ ! -d "$(model_dir "$model")" ]]; then echo "weights not found; downloading"; download_one "$model"; fi
  export HF_HUB_OFFLINE=1

  local status=0
  for e in ${exps//,/ }; do
    echo; echo "---- $e (T=0, seed 0) ----  $(date '+%T')"
    run_sharded "$model" "$e" "$tp" "$n" "${groups[@]}" -- --prompt normal || status=1
  done
  if [[ ",$exps," == *",exp2,"* && "$repeats" == "1" ]]; then
    for s in 1 2 3; do
      echo; echo "---- exp2 repeat T=0.7 seed $s ----  $(date '+%T')"
      run_sharded "$model" exp2 "$tp" "$n" "${groups[@]}" -- --prompt normal --temperature 0.7 --seed "$s" || status=1
    done
  fi
  echo; echo "---- official scoring ----"
  for e in ${exps//,/ }; do python -m score.score_all --exp "$e" --model "$model" --no-figures || true; done
  if [[ "$cleanup" == "1" ]]; then
    if [[ $status == 0 ]] && complete "$model" "$exps"; then cmd_cleanup "$model"
    else echo "not deleting the weights: some runs are incomplete"; fi
  fi
  echo "== $(date '+%F %T') finished $model (status $status) =="
  return $status
}

complete() {   # all expected answers saved (or listed as skipped) for this model?
  python - "$1" "$2" "$(cfg outputs.answers)" <<'PY'
import json, sys
from pathlib import Path
model, exps, root = sys.argv[1], sys.argv[2].split(","), Path(sys.argv[3])
exp_n = {"exp2": 1440, "exp3": 3840, "exp4": 960, "exp6": 1500}
ok = True
for e in exps:
    f = root / e / model / "normal_t0_s0.jsonl"
    n = sum(1 for _ in open(f)) if f.exists() else 0
    sk = f.with_suffix(".skipped.json")
    skipped_docs = len(json.loads(sk.read_text())) if sk.exists() else 0
    q_per_doc = 1 if e == "exp6" else 12
    ok &= n + skipped_docs * q_per_doc >= exp_n.get(e, 0)
sys.exit(0 if ok else 1)
PY
}

# ----------------------------------------------------------------------------- submit
cmd_submit() {
  need_env
  local models="$ALL_MODELS" exps="exp2,exp3,exp4" repeats=1 chain=0 dry=0 gpus="" hours="" cleanup=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --models) models="${2//,/ }"; shift ;;
      --exps) exps="$2"; shift ;;
      --gpus) gpus="$2"; shift ;;
      --hours) hours="$2"; shift ;;
      --no-repeats) repeats=0 ;;
      --cleanup) cleanup=1 ;;
      --chain) chain=1 ;;
      --dry-run) dry=1 ;;
      *) echo "unknown option $1"; exit 1 ;;
    esac; shift
  done
  local part acct qos maxg; part="$(cfg slurm.partition)"; acct="$(cfg slurm.account)"; qos="$(cfg slurm.qos)"
  maxg="$(cfg slurm.max_gpus_per_job)"; maxg="${maxg:-4}"
  local logdir="$PROJECT_ROOT/logs/slurm"; mkdir -p "$logdir"
  local prev="" total_gpuh=0
  for m in $ALL_MODELS; do
    [[ " $models " == *" $m "* ]] || continue
    local tp; tp="$(tp_for "$m")"
    local g="${gpus:-$(( 2 * tp ))}"; (( g > maxg )) && g=$maxg; (( g < tp )) && g=$tp
    g=$(( g / tp * tp ))                                 # whole copies only
    local copies=$(( g / tp ))
    local h="${hours:-$(hours_for "$m" "$copies")}"
    local mem=$(( 64 * g + ( $(mcfg "$m" params_b) > 40 ? 128 : 32 ) ))
    local args=(--job-name="ns-$m" --partition="$part" --gres="gpu:$g" --nodes=1 --ntasks=1
                --cpus-per-task=$(( 8 * g )) --mem="${mem}G" --time="$h:00:00" --output="$logdir/%x-%j.out")
    [[ -n "$acct" ]] && args+=(--account="$acct")
    [[ -n "$qos" ]] && args+=(--qos="$qos")
    [[ $chain == 1 && -n "$prev" ]] && args+=(--dependency="afterany:$prev")
    args+=(--wrap="cd '$PROJECT_ROOT' && source \"\$(conda info --base)/etc/profile.d/conda.sh\" && conda activate nullscale && bash scripts/run_h200.sh job $m $exps $repeats $cleanup")
    total_gpuh=$(( total_gpuh + g * h ))
    if [[ $dry == 1 ]]; then
      echo "# $m: $g x H200 = $copies copies x tp $tp, up to ${h}h (at most $(( g * h )) GPU-hours)"
      echo "sbatch ${args[*]}"; echo
      prev="DRYRUN"
    else
      prev="$(sbatch --parsable "${args[@]}")"
      echo "submitted $m: job $prev  ($g x H200, $copies copies, ${h}h limit)  log: logs/slurm/ns-$m-$prev.out"
    fi
  done
  echo "Upper bound if every job used its full time: $total_gpuh GPU-hours (real use is much lower; quota left ~32,500)."
  [[ $dry == 1 ]] || echo "Watch: squeue -u \$USER     Progress: bash scripts/run_h200.sh status"
}

# ----------------------------------------------------------------------------- status
cmd_status() {
  need_env
  local ans; ans="$(cfg outputs.answers)"
  count() {   # main file + any unmerged part files
    local n=0 f; for f in "$1" "${1%.jsonl}".part*of*.jsonl; do [[ -f "$f" ]] && n=$(( n + $(wc -l < "$f") )); done; echo $n
  }
  printf "%-16s %-14s %-14s %-14s %-24s\n" model exp2 exp3 exp4 "exp2 T=0.7 seeds 1/2/3"
  for m in $ALL_MODELS; do
    row=()
    for e in exp2 exp3 exp4; do
      f="$ans/$e/$m/normal_t0_s0.jsonl"; sk=""; [[ -f "${f%.jsonl}.skipped.json" ]] && sk="*"
      row+=("$(count "$f")/$(eval echo \$EXPECTED_$e)$sk")
    done
    rep=""; for s in 1 2 3; do rep+="$(count "$ans/exp2/$m/normal_t0.7_s$s.jsonl") "; done
    printf "%-16s %-14s %-14s %-14s %-24s\n" "$m" "${row[0]}" "${row[1]}" "${row[2]}" "$rep"
  done
  echo "(* = some documents skipped because they do not fit the model's window; see the .skipped.json file)"
  command -v squeue >/dev/null && { echo; squeue -u "$USER" -o "%.10i %.18j %.8T %.10M %.10l %.6b %R"; } || true
}

case "${1:-}" in
  check) cmd_check ;;
  download) shift; cmd_download "${1:-}" ;;
  cleanup) shift; need_env; for m in ${1//,/ }; do cmd_cleanup "$m"; done ;;
  build) cmd_build ;;
  submit) shift; cmd_submit "$@" ;;
  job) shift; cmd_job "$@" ;;
  status) cmd_status ;;
  *) sed -n '2,38p' "$0"; exit 1 ;;
esac

# Note on 128K: Gemma and Qwen split every digit into its own token, so a 128K (Llama-token) document is
# ~156K Gemma tokens; GLM-4.5-Air needs ~133K. Gemma 3 27B and GLM-4.5-Air have 131,072-token windows,
# so their 128K Exp 3 documents are skipped. The proposed fix (top length ~104K for all models) changes
# configs/experiments.yaml and needs Exp 3 rebuilt; decide before those two models run Exp 3.
