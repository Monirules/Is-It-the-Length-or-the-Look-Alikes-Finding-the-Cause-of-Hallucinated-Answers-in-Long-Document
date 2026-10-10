from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_EXP = {"E1_lookalike_level": "exp2", "E2_length_filler": "exp3", "E3_copies": "exp4",
            "E4_wikipedia": "exp6", "E5_protocol": "exp7", "E6_decoy_control": "exp8"}
COLUMNS = ["qid", "ladder", "level", "copies", "filler", "length_k", "answerable", "field", "question", "gold",
           "lookalike_values", "response", "answer_part", "label", "outcome", "captured", "mentions_lookalike",
           "source", "refusal", "hedged", "truncated", "n_prompt_tokens", "cached_prompt_tokens"]


def cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=str(PROJECT_ROOT / "release"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "results_release"))
    a = ap.parse_args(argv)
    n_files = n_rows = 0
    for f in sorted(Path(a.release, "scored").glob("*/*/*.scored.jsonl.gz")):
        exp = CODE_EXP.get(f.parts[-3])
        if exp is None:
            continue
        model = f.parts[-2]
        run = f.name[: -len(".scored.jsonl.gz")]
        d = Path(a.out) / f"{exp}_{model}_{run}"
        d.mkdir(parents=True, exist_ok=True)
        with gzip.open(f, "rt", encoding="utf-8") as fi, open(d / "scored.csv", "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(COLUMNS)
            for line in fi:
                r = json.loads(line)
                w.writerow([cell(r.get(c)) for c in COLUMNS])
                n_rows += 1
        n_files += 1
    print(f"{n_files} runs, {n_rows:,} answers -> {a.out}")
    print(f"next: python -m analysis.main_results --results {a.out}")


if __name__ == "__main__":
    main()
