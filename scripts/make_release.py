"""scripts/make_release.py

Packs the raw model responses and the scored answers of the seven-model runs into release/, the folder
that the README describes. Run it once where the answers live (the machine that ran run/run_vllm.py and
score/score_all.py), then commit release/.

  python scripts/make_release.py                       # work folder from configs/paths.yaml
  python scripts/make_release.py --work /path/to/nullscale_work --out release

What it writes
  release/responses/<E>/<model>/<run>.jsonl.gz      raw answers, one JSON line per answer (run/run_vllm.py)
  release/responses/<E>/<model>/<run>.meta.json     run settings, package versions, timings
  release/scored/<E>/<model>/<run>.scored.jsonl.gz  the same answers with the scoring fields (score/score_all.py)
  release/MANIFEST.csv                              one row per file: experiment, model, run, answers, sha256

<E> is the experiment number used in the paper (code folder in brackets):
  E1_lookalike_level [exp2]  E2_length_filler [exp3]  E3_copies [exp4]  E4_wikipedia [exp6]  E5_protocol [exp7]

Anonymity: absolute paths are cut to their file name, and the host name and the command line are dropped
from the .meta.json files. No other field is changed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

PAPER_EXP = {"exp2": "E1_lookalike_level", "exp3": "E2_length_filler", "exp4": "E3_copies",
             "exp6": "E4_wikipedia", "exp7": "E5_protocol"}
ABS_PATH = re.compile(r"(?:/home|/N|/mnt|/scratch|/Users|/sessions|/tmp|[A-Za-z]:\\)[^\s\"']*[/\\]([^/\\\s\"']+)")
DROP_META = {"argv", "host"}


def scrub(x):
    if isinstance(x, str):
        return ABS_PATH.sub(r"\1", x)
    if isinstance(x, list):
        return [scrub(v) for v in x]
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items()}
    return x


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pack_jsonl(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(src, encoding="utf-8") as fi, gzip.open(dst, "wt", encoding="utf-8", compresslevel=9) as fo:
        for line in fi:
            if line.strip():
                fo.write(json.dumps(scrub(json.loads(line)), ensure_ascii=False) + "\n")
                n += 1
    return n


def runs(root: Path, suffix: str):
    """<root>/<exp>/<model>/<run><suffix>, merged files only (no shard parts)."""
    for f in sorted(root.glob(f"*/*/*{suffix}")):
        if re.search(r"\.part\d+of\d+\.", f.name) or f.parent.name == "parts":
            continue
        exp, model = f.parts[-3], f.parts[-2]
        if exp in PAPER_EXP:
            yield exp, model, f.name[: -len(suffix)], f


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", help="work folder holding outputs/answers and outputs/scores")
    ap.add_argument("--out", default=str(PROJECT_ROOT / "release"))
    a = ap.parse_args(argv)
    if a.work:
        answers, scores = Path(a.work) / "outputs" / "answers", Path(a.work) / "outputs" / "scores"
    else:
        from nullscale.config import load_paths
        P = load_paths()
        answers, scores = Path(P["outputs"]["answers"]), Path(P["outputs"]["scores"])
    out = Path(a.out)
    manifest = []

    for exp, model, run, f in runs(answers, ".jsonl"):
        if run.endswith((".scored", ".skipped", ".meta")):
            continue
        dst = out / "responses" / PAPER_EXP[exp] / model / f"{run}.jsonl.gz"
        n = pack_jsonl(f, dst)
        manifest.append(("responses", PAPER_EXP[exp], exp, model, run, n, dst))
        meta = f.with_suffix(".meta.json")
        if meta.exists():
            m = {k: v for k, v in json.loads(meta.read_text(encoding="utf-8")).items() if k not in DROP_META}
            (dst.parent / f"{run}.meta.json").write_text(json.dumps(scrub(m), indent=1), encoding="utf-8")
        print(f"responses  {PAPER_EXP[exp]:<20} {model:<22} {run:<22} {n:>6} answers")

    for exp, model, run, f in runs(scores, ".scored.jsonl"):
        dst = out / "scored" / PAPER_EXP[exp] / model / f"{run}.scored.jsonl.gz"
        n = pack_jsonl(f, dst)
        manifest.append(("scored", PAPER_EXP[exp], exp, model, run, n, dst))
        print(f"scored     {PAPER_EXP[exp]:<20} {model:<22} {run:<22} {n:>6} answers")

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "MANIFEST.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "paper_experiment", "code_experiment", "model", "run", "answers", "file", "bytes", "sha256"])
        for kind, pe, ce, model, run, n, p in manifest:
            w.writerow([kind, pe, ce, model, run, n, p.relative_to(out).as_posix(), p.stat().st_size, sha256(p)])
    tot = lambda k: sum(r[5] for r in manifest if r[0] == k)
    print(f"\n{len(manifest)} files; {tot('responses'):,} raw answers, {tot('scored'):,} scored answers -> {out}")


if __name__ == "__main__":
    main()
