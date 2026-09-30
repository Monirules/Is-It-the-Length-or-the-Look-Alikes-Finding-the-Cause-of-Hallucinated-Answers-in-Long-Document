#!/usr/bin/env bash
# scripts/setup_env.sh  (owner: Monirul)
#
# Creates the conda env "nullscale" (Python 3.11, vLLM, PyTorch, Transformers, pandas, statsmodels,
# rank_bm25, ...) and checks that the GPU, vLLM and Hugging Face access all work.
#
# Run from the project folder, in Linux (WSL2 Ubuntu on the PC, or the cluster):
#   bash scripts/setup_env.sh pc              # RTX 5070 PC
#   bash scripts/setup_env.sh pc --smoke      # + load Qwen3 4B in FP8 and generate one answer
#   bash scripts/setup_env.sh cluster         # cluster login node (install only)
#   bash scripts/setup_env.sh cluster --smoke # inside a GPU job: + one answer from Qwen3 4B
#
# Safe to run again: an existing env is reused, packages are only upgraded if missing.
# Every run writes a log to logs/setup_<profile>_<time>.log and the exact package versions
# to logs/pip_freeze_<profile>.txt (put that file in git so Jayden's env matches).

set -euo pipefail

PROFILE="${1:-}"
SMOKE=0
[[ "${2:-}" == "--smoke" ]] && SMOKE=1
if [[ "$PROFILE" != "pc" && "$PROFILE" != "cluster" ]]; then
  echo "usage: bash scripts/setup_env.sh pc|cluster [--smoke]"; exit 1
fi

ENV_NAME="${ENV_NAME:-nullscale}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$PROJECT_ROOT/logs"
LOG="$PROJECT_ROOT/logs/setup_${PROFILE}_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
step() { echo; echo "================ $* ================"; }

step "1/6 Find conda"
if ! command -v conda >/dev/null 2>&1; then
  if command -v module >/dev/null 2>&1; then          # cluster: conda usually comes from a module
    module load anaconda3 2>/dev/null || module load miniconda3 2>/dev/null || module load anaconda 2>/dev/null || true
  fi
fi
if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. On the PC install Miniconda inside WSL first (see the instructions you were given)."
  echo "On the cluster run 'module avail' and load the conda/anaconda module, then run this again."
  exit 1
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
echo "conda: $(conda --version)"

step "2/6 Create or reuse env '$ENV_NAME' (Python 3.11)"
if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "env exists, reusing it"
else
  conda create -y -n "$ENV_NAME" python=3.11
fi
conda activate "$ENV_NAME"
python --version

step "3/6 Install packages"
python -m pip install --upgrade pip
# vLLM brings a matching PyTorch built for CUDA 12.8+, which the RTX 5070 (Blackwell, sm_120) needs.
# >=0.10.2 is required for Qwen3-Next.
python -m pip install "vllm>=0.10.2"
python -m pip install transformers pandas statsmodels rank_bm25 pyyaml "huggingface_hub[cli]" \
                      scipy matplotlib pytest tqdm
python -m pip freeze > "$PROJECT_ROOT/logs/pip_freeze_${PROFILE}.txt"
echo "package versions saved to logs/pip_freeze_${PROFILE}.txt"

step "4/6 Link the project and set env variables"
# A .pth file makes 'import nullscale' work from anywhere (safe with the spaces in the OneDrive path).
SITE="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "$PROJECT_ROOT" > "$SITE/nullscale_project.pth"
HF_HOME_DIR="$(python -m nullscale.config --profile "$PROFILE" --get hf_home)"
conda env config vars set NULLSCALE_PROFILE="$PROFILE" HF_HOME="$HF_HOME_DIR" >/dev/null
conda deactivate && conda activate "$ENV_NAME"      # reload so the variables are active now
echo "NULLSCALE_PROFILE=$NULLSCALE_PROFILE"
echo "HF_HOME=$HF_HOME"
python -m nullscale.config --make-dirs >/dev/null && echo "data/output folders created"

step "5/6 Check GPU, PyTorch and vLLM"
python - <<'PY'
import torch, importlib
print(f"torch {torch.__version__}  (built for CUDA {torch.version.cuda})")
for pkg in ("vllm", "transformers", "pandas", "statsmodels", "rank_bm25"):
    try:
        m = importlib.import_module(pkg)
        print(f"{pkg:<13}{getattr(m, '__version__', 'ok')}")
    except Exception as e:
        print(f"{pkg:<13}IMPORT FAILED: {e}")
if not torch.cuda.is_available():
    print("NO GPU visible. Fine on a cluster login node; on the PC this is a problem (see nvidia-smi).")
else:
    for i in range(torch.cuda.device_count()):
        cap = torch.cuda.get_device_capability(i)
        mem = torch.cuda.get_device_properties(i).total_memory / 1e9
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}  {mem:.1f} GB  compute {cap[0]}.{cap[1]}")
        arch = f"sm_{cap[0]}{cap[1]}"
        if arch not in torch.cuda.get_arch_list():
            print(f"  PROBLEM: this PyTorch has no kernels for {arch}. Needs a CUDA 12.8+ build.")
    x = torch.randn(1024, 1024, device="cuda"); (x @ x).sum().item()
    print("matmul on GPU: ok")
PY

step "6/6 Hugging Face login and licence access"
python - <<'PY'
from huggingface_hub import whoami
try:
    print("logged in as:", whoami()["name"])
except Exception:
    print("NOT logged in. Run:  hf auth login   (or: huggingface-cli login), then run this script again.")
    raise SystemExit(0)
from nullscale.config import load_models
try:
    from huggingface_hub import auth_check
except ImportError:
    auth_check = None
repos = []
for k, m in load_models()["open_models"].items():
    repos += [m["hf_id"]] + ([m["base_hf_id"]] if m["base_hf_id"] != m["hf_id"] else [])
for repo in dict.fromkeys(repos):
    if auth_check is None:
        print(f"  {repo}: (huggingface_hub too old to check)"); continue
    try:
        auth_check(repo); print(f"  OK       {repo}")
    except Exception as e:
        kind = type(e).__name__
        hint = "accept the licence on the model page" if "Gated" in kind else "check the repo name"
        print(f"  MISSING  {repo}  ({kind}: {hint})")
PY

if [[ "$SMOKE" == "1" ]]; then
  step "Smoke test: Qwen3 4B answers one question"
  # vLLM starts its engine in a fresh "spawned" process (always on WSL), which re-imports the calling
  # script. So the test must be a real .py file with a __main__ guard, not code piped into python.
  SMOKE_PY="$(mktemp --suffix=_nullscale_smoke.py)"
  cat > "$SMOKE_PY" <<'PY'
import os, time


def main():
    from vllm import SamplingParams
    from run.run_vllm import engine_settings, make_llm
    pc = os.environ.get("NULLSCALE_PROFILE") == "pc"
    kw, info = engine_settings("qwen3_4b", "pc" if pc else "cluster", 4096, None, None)
    t = time.time()
    llm = make_llm(kw)
    print(f"loaded in {time.time()-t:.0f}s ({info['quantization']})")
    doc = "Lease record. Tenant: Harbor Lane Bakery. Building: Elm Court. Monthly rent: $4,200."
    msgs = [[{"role": "user", "content": f"{doc}\n\nWhat is the monthly rent for Harbor Lane Bakery? "
                                         "Answer only from the text."}],
            [{"role": "user", "content": f"{doc}\n\nWhat is the monthly rent for Quarry Point Florist? "
                                         "Answer only from the text. If it is not in the text, say NOT FOUND."}]]
    outs = llm.chat(msgs, SamplingParams(temperature=0.0, max_tokens=40))
    for label, o in zip(["answerable", "unanswerable"], outs):
        print(f"{label:>13}: {o.outputs[0].text.strip()!r}")
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
PY
  python "$SMOKE_PY"
  rm -f "$SMOKE_PY"
fi

step "Done"
echo "Log: $LOG"
echo "Next: conda activate $ENV_NAME && python -m nullscale.config"
