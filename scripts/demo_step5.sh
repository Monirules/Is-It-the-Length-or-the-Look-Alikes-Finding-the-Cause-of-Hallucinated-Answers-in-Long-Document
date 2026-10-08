#!/usr/bin/env bash
# scripts/demo_step5.sh
# Step 5 in one go: question bank, absence tests, full dataset build, and a re-check of every saved
# document. Output is also saved to logs/step5_demo_<time>.txt.
# Run from the project folder, inside the nullscale conda env (Ubuntu/WSL). No GPU needed.
#   bash scripts/demo_step5.sh            # everything (the build takes a few minutes)
#   bash scripts/demo_step5.sh --quick    # small build (6 documents per experiment) to try it first
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
mkdir -p logs
OUT="logs/step5_demo_$(date +%Y%m%d_%H%M%S).txt"
LIMIT=""
[[ "${1:-}" == "--quick" ]] && LIMIT="--limit 6"
DATA="$(python -m nullscale.config --get data.nullscale)"
{
  echo "######## 1. questions.py: template bank and one document's 12 questions ########"
  python -m nullscale.questions
  echo; echo "######## 2. tests/test_absence.py: 100 random documents + planted-error tests ########"
  python -m pytest tests/test_absence.py -v
  echo; echo "######## 3. build_dataset.py: every NullScale experiment ########"
  python -m nullscale.build_dataset --exp all $LIMIT
  echo; echo "######## 4. absence_check.py: re-check every saved document from disk ########"
  python -m nullscale.absence_check "$DATA" | tail -3
  echo; echo "######## 5. make_figures.py: pipeline, ladders, dataset checks, composition ########"
  python scripts/make_figures.py
  echo; echo "Dataset folder: $DATA"
  echo "Figures folder: $PROJECT_ROOT/outputs/figures"
} 2>&1 | tee "$OUT"
echo; echo "Saved: $OUT"
