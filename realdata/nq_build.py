"""realdata/nq_build.py

Exp 6, part 1: takes 300 Natural Questions items, removes EVERY passage that holds the answer, and saves
the questions.

Source
  Natural Questions (Kwiatkowski et al., 2019), open-domain version with 100-word Wikipedia passages, as
  released by DPR (Karpukhin et al., 2020) and packaged by Tevatron on Hugging Face:
  Tevatron/wikipedia-nq, file nq-dev.jsonl.gz (150 MB; 6,515 questions). Each question comes with its
  answers, the passages that contain an answer ("positive"), and ~100 BM25-retrieved Wikipedia passages
  ("negative"): similar passages that do not contain the answer. We use the dev split because these
  questions were never used to train DPR's retriever.

Removing the answer (strict; three rules, all applied)
  1. every positive passage is removed;
  2. every passage whose text or title contains ANY answer string is removed (lower case, no punctuation,
     no articles, whole words: the standard DPR "has_answer" test);
  3. every passage from the same Wikipedia article as a positive passage is removed, because other parts
     of that article often imply the answer.
  retrieve.py checks the finished documents again.

Which questions (fixed seed; base_seed + Exp 6 seed_offset from configs/experiments.yaml)
  - at least one answer that can be searched safely (not a 1-2 digit number, not a single letter);
  - short answer (the shortest answer has at most 5 words);
  - at least one positive passage that contains the answer (it is the gold passage of the control setting);
  - at least 40 similar passages left after removing the answer.

Output (in paths.yaml data.nq; PC: ~/nullscale_work/data/nq)
  nq300.jsonl          the 300 questions: nq_id, question, answers, gold passage, gold titles, similar
                       passage ids (DPR order, answer removed), counts of removed passages
  pool.jsonl.gz        every distinct passage of the dev file (~600,000): the Wikipedia pool for retrieve.py
  outputs/realdata/nq_build_report.md   (project folder) what was kept and removed, with examples

Usage (Ubuntu/WSL, nullscale env, project folder; no GPU; 3-6 minutes)
  python -m realdata.nq_build
  python -m realdata.nq_build --input /path/to/nq-dev.jsonl.gz      # use a file you downloaded yourself
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from realdata.common import OUT_DIR, holds_answer, normalize, read_jsonl_gz, usable_answers, write_jsonl  # noqa: E402

REPO, FILE = "Tevatron/wikipedia-nq", "nq-dev.jsonl.gz"
URL = f"https://huggingface.co/datasets/{REPO}/resolve/main/{FILE}"
MIN_SIMILAR = 40
MAX_ANSWER_WORDS = 5


def nq_root() -> Path:
    try:
        from nullscale.config import load_paths
        return Path(load_paths()["data"]["nq"])
    except Exception:
        return Path.home() / "nullscale_work" / "data" / "nq"


def exp6_seed() -> int:
    try:
        from nullscale.config import load_experiments
        e = load_experiments()
        return int(e["defaults"]["base_seed"]) + int(e["experiments"]["exp6"]["seed_offset"])
    except Exception:
        return 20261012 + 6000


def fetch(root: Path) -> Path:
    dest = root / "raw" / FILE
    if dest.exists() and dest.stat().st_size > 100_000_000:
        print(f"using {dest} ({dest.stat().st_size / 1e6:.0f} MB)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
        p = Path(hf_hub_download(REPO, FILE, repo_type="dataset", local_dir=str(dest.parent)))
        print(f"downloaded {p} ({p.stat().st_size / 1e6:.0f} MB)")
        return p
    except Exception as e:
        print(f"(huggingface_hub download failed: {e}; trying a plain download)")
    import urllib.request
    urllib.request.urlretrieve(URL, dest)
    print(f"downloaded {dest} ({dest.stat().st_size / 1e6:.0f} MB)")
    return dest


def clean_question(q: str) -> str:
    q = " ".join(q.split())
    q = q[0].upper() + q[1:] if q else q
    return q if q.endswith("?") else q + "?"


def process(item: dict) -> dict | None:
    """Apply the three removal rules to one NQ item. Returns None if the item does not qualify."""
    answers = usable_answers(item.get("answers") or [])
    if not answers or min(len(normalize(a).split()) for a in answers) > MAX_ANSWER_WORDS:
        return None
    pos = item.get("positive_passages") or []
    gold = [p for p in pos if holds_answer(p.get("text", ""), answers)]
    if not gold:
        return None
    gold_titles = sorted({p.get("title", "") for p in pos})
    removed = Counter(positive=len(pos))
    similar = []
    for p in item.get("negative_passages") or []:
        if holds_answer(p.get("text", ""), answers, p.get("title", "")):
            removed["holds_answer"] += 1
        elif p.get("title", "") in gold_titles:
            removed["same_article"] += 1
        else:
            similar.append(p["docid"])
    if len(similar) < MIN_SIMILAR:
        return None
    g = gold[0]
    return {
        "nq_id": str(item.get("query_id")), "question": clean_question(item["query"]), "answers": answers,
        "all_answers": item.get("answers"), "gold_passage": {"docid": g["docid"], "title": g.get("title", ""), "text": g["text"]},
        "gold_titles": gold_titles, "similar_ids": similar, "removed": dict(removed),
        "n_negatives": len(item.get("negative_passages") or []),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="a local nq-dev.jsonl.gz (default: download from Hugging Face)")
    ap.add_argument("--out", help="output folder (default: paths.yaml data.nq)")
    ap.add_argument("--n", type=int, default=None, help="number of questions (default: experiments.yaml exp6 n_questions = 300)")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args(argv)
    root = Path(a.out) if a.out else nq_root()
    root.mkdir(parents=True, exist_ok=True)
    n_want = a.n
    if n_want is None:
        try:
            from nullscale.config import load_experiments
            n_want = int(load_experiments()["experiments"]["exp6"]["n_questions"])
        except Exception:
            n_want = 300
    seed = a.seed if a.seed is not None else exp6_seed()
    src = Path(a.input) if a.input else fetch(root)

    t0 = time.time()
    pool: dict[str, dict] = {}
    candidates, reasons, n_items = [], Counter(), 0
    for item in read_jsonl_gz(src):
        n_items += 1
        for p in (item.get("positive_passages") or []) + (item.get("negative_passages") or []):
            if p["docid"] not in pool:
                pool[p["docid"]] = {"docid": p["docid"], "title": p.get("title", ""), "text": p.get("text", "")}
        r = process(item)
        if r is None:
            reasons["did not qualify"] += 1
        else:
            candidates.append(r)
        if n_items % 1000 == 0:
            print(f"  read {n_items:,} questions, {len(pool):,} passages ({time.time() - t0:.0f}s)", flush=True)
    print(f"{n_items:,} questions read; {len(candidates):,} qualify; pool of {len(pool):,} distinct passages")
    if len(candidates) < n_want:
        sys.exit(f"only {len(candidates)} questions qualify, need {n_want}")
    rng = random.Random(seed)
    chosen = rng.sample(candidates, n_want)
    chosen.sort(key=lambda r: int(r["nq_id"]) if r["nq_id"].isdigit() else r["nq_id"])
    for i, r in enumerate(chosen):
        r["idx"] = i
    write_jsonl(root / "nq300.jsonl", chosen)
    write_jsonl(root / "pool.jsonl.gz", pool.values())
    print(f"saved {root / 'nq300.jsonl'} and {root / 'pool.jsonl.gz'} ({time.time() - t0:.0f}s)")

    # report
    rem = Counter()
    for r in chosen:
        rem.update(r["removed"])
    sims = sorted(len(r["similar_ids"]) for r in chosen)
    L = ["# Exp 6 data, part 1: Natural Questions with the answer removed", "",
         f"Source: `{REPO}` / `{FILE}` (DPR's open-domain Natural Questions, dev split). Seed {seed}.", "",
         f"- questions read: {n_items:,}; qualifying: {len(candidates):,}; **chosen: {len(chosen)}**",
         f"- Wikipedia pool for retrieve.py: {len(pool):,} distinct 100-word passages",
         f"- passages removed from the chosen questions' similar lists: {rem['positive']:,} positive (gold), "
         f"{rem['holds_answer']:,} holding an answer string, {rem['same_article']:,} from the gold article",
         f"- similar passages left per question: min {sims[0]}, median {sims[len(sims) // 2]}, max {sims[-1]}", "",
         "## Ten examples", "", "| # | question | answers | gold article | similar passages left |", "|---|---|---|---|---|"]
    for r in chosen[:10]:
        L.append(f"| {r['idx']} | {r['question']} | {'; '.join(r['answers'][:3])} | {'; '.join(r['gold_titles'][:2])} | {len(r['similar_ids'])} |")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "nq_build_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nsaved {OUT_DIR / 'nq_build_report.md'}\nNext:  python -m realdata.retrieve")


if __name__ == "__main__":
    main()
