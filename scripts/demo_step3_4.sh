#!/usr/bin/env bash
# scripts/demo_step3_4.sh
# Runs every Step 3-4 generator check in order and saves all output to logs/step3_4_demo_<time>.txt.
# Run from the project folder, inside the nullscale conda env (WSL on the PC). No GPU needed.
#   bash scripts/demo_step3_4.sh
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
OUT="logs/step3_4_demo_$(date +%Y%m%d_%H%M%S).txt"
DEMO="$PROJECT_ROOT/data/nullscale/demo"   # inside the project folder, so you can open the documents from Windows
mkdir -p logs
{
  echo "######## 1. schema.py: the fake business world ########";      python -m nullscale.schema
  echo; echo "######## 2. records.py: no two names accidentally similar ########"; python -m nullscale.records
  echo; echo "######## 3. render.py: 10 readable fake records ########";  python -m nullscale.render
  echo; echo "######## 4. lookalike.py: both ladders, four levels ########"; python -m nullscale.lookalike
  echo; echo "######## 5. filler.py: unrelated vs sibling at equal size ########"; python -m nullscale.filler
  echo; echo "######## 6. assemble.py: one 32K document with a strong look-alike ########"
  python -m nullscale.assemble --length 32 --ladder name --level strong --filler unrelated --seed 1 --out "$DEMO"
  echo; echo "######## 7. assemble.py: all 16 ladder x level x filler documents at 32K ########"
  python -m nullscale.assemble --demo --length 32 --seed 1 --out "$DEMO"
  echo; echo "######## 8. assemble.py: the other lengths (8K, 64K, 128K) ########"
  for L in 8 64 128; do python -m nullscale.assemble --length $L --ladder role --level strong --filler sibling --seed 1 --out "$DEMO" | grep -E "^(ladder|name|role) "; done
  echo; echo "######## 9. assemble.py: eight copies of the look-alike (Exp 4) ########"
  python -m nullscale.assemble --length 32 --ladder name --level strong --copies 8 --seed 1 --out "$DEMO" | grep -E "^(ladder|name|role) "
} 2>&1 | tee "$OUT"
echo; echo "Saved: $OUT"
