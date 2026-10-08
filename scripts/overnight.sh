#!/usr/bin/env bash
# scripts/overnight.sh
#
# One overnight pipeline on the cluster for the professor's most important to-do items.
#   1. preflight  adds the llama33_70b_bf16 entry to configs/models.yaml (once), checks the HF login,
#                 the free space on scratch and the Experiment 2 (code exp3) 128K data
#   2. cpu        runs analysis/overnight_checks.py at once (ladder split, three-way outcome, exchange rate
#                 robustness, signal detection, bootstrap breaking lengths, RIKER2 per model, token counts,
#                 clean-arm check, Llama 128K audit)            -> outputs/overnight/
#   3. download   bf16 weights of Llama 3.3 70B (about 140 GB, about 1 hour) on the login node
#   4. submit     one Slurm job, 2 x H200, 8 h limit: Llama 3.3 70B in bf16 on the 128K documents of
#                 code exp3 (no look-alike and strong, 80 documents, 960 answers), scoring, then step 2 again
#                 so the morning report includes FP8 against bf16
#
# Run on the cluster LOGIN node, from the project folder, inside the conda env, and let it run while you sleep:
#   conda activate nullscale
#   nohup bash scripts/overnight.sh all > logs/overnight.log 2>&1 &
# Other commands:
#   bash scripts/overnight.sh preflight     checks only (run this first, takes seconds)
#   bash scripts/overnight.sh cpu           CPU checks only
#   bash scripts/overnight.sh status        progress of the GPU job and the answer count
#   bash scripts/overnight.sh job           (internal) what the GPU node runs
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export NULLSCALE_PROFILE=cluster TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
MODEL=llama33_70b_bf16
EXPECTED=960
mkdir -p logs/slurm outputs/overnight

cfg() { python -m nullscale.config --profile cluster --get "$1" 2>/dev/null || true; }
need_env() { [[ "${CONDA_DEFAULT_ENV:-}" == "nullscale" ]] || { echo "Please run:  conda activate nullscale"; exit 1; }; }
answers_file() { echo "$(cfg outputs.answers)/exp3/$MODEL/normal_t0_s0.jsonl"; }
count() { local f="$1" n=0 x; for x in "$f" "${f%.jsonl}".part*of*.jsonl; do [[ -f "$x" ]] && n=$(( n + $(wc -l < "$x") )); done; echo $n; }

cmd_preflight() {
  need_env
  echo "== preflight $(date '+%F %T') =="
  # 1. models.yaml entry (inserted once, right before qwen3_next_80b, so nothing else changes)
  if ! grep -q "^  $MODEL:" configs/models.yaml; then
    python - <<'PY'
from pathlib import Path
p = Path("configs/models.yaml")
s = p.read_text(encoding="utf-8")
block = """  llama33_70b_bf16:              # overnight audit: same model as llama33_70b, full bf16 weights, 2 x H200
    family: llama
    hf_id: meta-llama/Llama-3.3-70B-Instruct
    base_hf_id: meta-llama/Llama-3.3-70B-Instruct
    gated: true
    params_b: 70
    active_params_b: 70
    max_model_len: 131072
    roig_fab_32k: 41.67
    pc:     {runnable: false}
    cluster: {dtype: bfloat16, tp_h200: 2, tp_a100: 4}
    vllm_args: {}

"""
anchor = "  qwen3_next_80b:"
assert anchor in s, "anchor qwen3_next_80b not found in configs/models.yaml"
p.write_text(s.replace(anchor, block + anchor, 1), encoding="utf-8")
print("added llama33_70b_bf16 to configs/models.yaml")
PY
  else
    echo "models.yaml already has $MODEL"
  fi
  python -c "from nullscale.config import load_models; m=load_models()['open_models']['$MODEL']; print('config ok:', m['hf_id'], m['cluster'])"
  # 2. Hugging Face login (Llama is gated)
  python -c "from huggingface_hub import whoami; print('HF login ok:', whoami()['name'])" \
    || { echo "Not logged in to Hugging Face. Run: hf auth login  (or huggingface-cli login)"; exit 1; }
  # 3. free space for about 140 GB of weights
  local hf; hf="$(cfg hf_home)"; mkdir -p "$hf"
  local free_gb; free_gb=$(df -BG --output=avail "$hf" | tail -1 | tr -dc '0-9')
  echo "free space at $hf: ${free_gb} GB (need about 150)"
  (( free_gb >= 150 )) || { echo "Not enough space. Free some with: bash scripts/run_h200.sh cleanup <model>"; exit 1; }
  # 4. the 128K documents of code exp3 must exist on the cluster
  python - <<'PY'
import json
from nullscale.config import load_paths
P = load_paths()
root = P["data"]["nullscale"] if isinstance(P.get("data"), dict) else None
from pathlib import Path
q = Path(root) / "exp3" / "questions.jsonl" if root else None
if not q or not q.exists():
    raise SystemExit(f"code exp3 questions not found at {q}")
n = sum(1 for l in open(q) if json.loads(l).get("length_k") == 128)
print(f"code exp3 data ok: {n} questions at 128K in {q}")
PY
  # 5. dry run of the runner (no model loaded)
  python -m run.run_vllm --model "$MODEL" --exp exp3 --lengths 128 --levels none,strong --profile cluster --dry-run | tail -5
  echo "preflight passed"
}

cmd_cpu() {
  need_env
  echo "== CPU checks $(date '+%F %T') =="
  python -m analysis.overnight_checks --results outputs/results_cluster --extra outputs/results --boot 2000 \
    > logs/overnight_checks.log 2>&1 && echo "done: outputs/overnight/report.md" \
    || { echo "CPU checks failed, see logs/overnight_checks.log"; tail -20 logs/overnight_checks.log; }
}

cmd_download() {
  need_env
  echo "== download $(date '+%F %T') =="
  bash scripts/run_h200.sh download "$MODEL"
  echo "download finished $(date '+%F %T')"
}

cmd_submit() {
  need_env
  local part acct qos; part="$(cfg slurm.partition)"; acct="$(cfg slurm.account)"; qos="$(cfg slurm.qos)"
  local args=(--job-name="ns-overnight-bf16" --partition="$part" --gres="gpu:2" --nodes=1 --ntasks=1
              --cpus-per-task=16 --mem=256G --time="8:00:00" --output="$PROJECT_ROOT/logs/slurm/%x-%j.out")
  [[ -n "$acct" ]] && args+=(--account="$acct")
  [[ -n "$qos" ]] && args+=(--qos="$qos")
  args+=(--wrap="cd '$PROJECT_ROOT' && source \"\$(conda info --base)/etc/profile.d/conda.sh\" && conda activate nullscale && bash scripts/overnight.sh job")
  local id; id="$(sbatch --parsable "${args[@]}")"
  echo "$id" > logs/overnight_jobid
  echo "submitted GPU job $id (2 x H200, 8 h limit). Log: logs/slurm/ns-overnight-bf16-$id.out"
}

cmd_job() {   # runs on the GPU node
  need_env
  export HF_HOME="$(cfg hf_home)" NULLSCALE_GPU_TYPE=h200 HF_HUB_OFFLINE=1
  export VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_USE_DEEP_GEMM=0          # same settings as run_h200.sh
  type module >/dev/null 2>&1 || source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
  module load gcc/11.3.0 2>/dev/null || true
  command -v nvcc >/dev/null 2>&1 || module load cuda 2>/dev/null || true
  command -v nvcc >/dev/null 2>&1 && export CUDA_HOME="${CUDA_HOME:-$(dirname "$(dirname "$(command -v nvcc)")")}"
  echo "== $(date '+%F %T') $MODEL, code exp3, 128K, none and strong, on $(hostname) =="
  nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true
  python -m run.run_vllm --model "$MODEL" --exp exp3 --lengths 128 --levels none,strong --profile cluster
  python -m score.score_all --exp exp3 --model "$MODEL" --no-figures
  cmd_cpu
  echo "== $(date '+%F %T') finished =="
}

cmd_status() {
  need_env
  echo "answers saved: $(count "$(answers_file)") of $EXPECTED"
  [[ -f logs/overnight_jobid ]] && squeue -j "$(cat logs/overnight_jobid)" 2>/dev/null || true
  squeue -u "$USER" -o "%.10i %.20j %.8T %.10M %.10l %.6b %R" 2>/dev/null || true
  ls -1 outputs/overnight 2>/dev/null | sed 's/^/  outputs\/overnight\//'
}

case "${1:-}" in
  preflight) cmd_preflight ;;
  cpu) cmd_cpu ;;
  download) cmd_download ;;
  submit) cmd_submit ;;
  job) cmd_job ;;
  status) cmd_status ;;
  all) cmd_preflight; cmd_cpu; cmd_download; cmd_submit
       echo "All started $(date '+%F %T'). In the morning: bash scripts/overnight.sh status" ;;
  *) sed -n '2,26p' "$0"; exit 1 ;;
esac
