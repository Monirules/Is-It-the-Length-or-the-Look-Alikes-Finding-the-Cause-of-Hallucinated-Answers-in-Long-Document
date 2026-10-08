"""run/merge_shards.py

Joins the answer files written by several GPUs at once (run_vllm.py --shard K --num-shards N) into the
one answers file every other script reads:
    <exp>/<model>/<prompt>_t<T>_s<seed>.part0of4.jsonl ... part3of4.jsonl  ->  <prompt>_t<T>_s<seed>.jsonl
Answers already in the main file are kept; a question answered twice is kept once. The part files are
then moved to <exp>/<model>/parts/ (not deleted), and their .skipped.json lists are combined.

Usage (any machine, no GPU)
  python -m run.merge_shards --exp exp3 --model qwen3_4b               # every run of that model/exp
  python -m run.merge_shards --exp exp2 --model qwen3_4b --stem normal_t0.7_s1
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

from nullscale.config import load_paths

PART_RE = re.compile(r"^(?P<stem>.+)\.part(?P<k>\d+)of(?P<n>\d+)\.jsonl$")


def merge_folder(folder: Path, only_stem: str | None = None) -> dict:
    groups: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(folder.glob("*.part*of*.jsonl")):
        m = PART_RE.match(p.name)
        if m and (only_stem is None or m["stem"] == only_stem):
            groups[m["stem"]].append(p)
    report = {}
    for stem, parts in groups.items():
        main = folder / f"{stem}.jsonl"
        seen = set()
        if main.exists():
            with open(main, encoding="utf-8") as f:
                seen = {json.loads(l)["qid"] for l in f if l.strip()}
        before = len(seen)
        added = 0
        skipped = []
        sk_main = folder / f"{stem}.skipped.json"
        if sk_main.exists():
            skipped = json.loads(sk_main.read_text(encoding="utf-8"))
        with open(main, "a", encoding="utf-8") as out:
            for p in parts:
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        qid = json.loads(line)["qid"]
                        if qid in seen:
                            continue
                        seen.add(qid)
                        out.write(line if line.endswith("\n") else line + "\n")
                        added += 1
                sk = p.with_name(p.name.replace(".jsonl", ".skipped.json"))
                if sk.exists():
                    skipped += json.loads(sk.read_text(encoding="utf-8"))
        if skipped:
            uniq = {s["doc_id"]: s for s in skipped}
            sk_main.write_text(json.dumps(list(uniq.values()), indent=1), encoding="utf-8")
        dest = folder / "parts"
        dest.mkdir(exist_ok=True)
        for p in parts:
            for side in (p, p.with_name(p.name.replace(".jsonl", ".meta.json")),
                         p.with_name(p.name.replace(".jsonl", ".skipped.json"))):
                if side.exists():
                    shutil.move(str(side), str(dest / side.name))
        report[stem] = {"parts": len(parts), "before": before, "added": added, "total": len(seen)}
        print(f"  {folder.parent.name}/{folder.name}/{stem}.jsonl: {before} + {added} = {len(seen)} answers "
              f"(from {len(parts)} part files; parts moved to parts/)")
    return report


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--stem", help="only this run, e.g. normal_t0_s0")
    ap.add_argument("--out", help="answers root (default: paths.yaml outputs.answers)")
    a = ap.parse_args(argv)
    root = Path(a.out or load_paths()["outputs"]["answers"])
    folder = root / a.exp / a.model
    if not folder.exists():
        raise SystemExit(f"no answers folder {folder}")
    rep = merge_folder(folder, a.stem)
    if not rep:
        print(f"  nothing to merge in {folder}")


if __name__ == "__main__":
    main()
