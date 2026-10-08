"""realdata/retrieve.py

Exp 6, part 2: for each of the 300 questions, finds Wikipedia passages that look like the answer's
passage (look-alikes) and random passages, and fills documents to exactly 8K and 32K tokens. The result
is the Exp 6 dataset, in the same format as the NullScale datasets, so run/run_vllm.py runs it directly.

The five settings (configs/experiments.yaml, exp6.settings), one document per question and setting:
  gold_present_8k        control: the gold passage (it holds the answer) + look-alike passages, 8K.
                         The model SHOULD answer.
  no_gold_lookalike_8k   gold removed; filled with look-alike passages, 8K
  no_gold_random_8k      gold removed; filled with random passages, 8K
  no_gold_lookalike_32k  as above, 32K
  no_gold_random_32k     as above, 32K
  -> 300 x 5 = 1,500 documents and 1,500 questions per model.

Look-alike passages, most similar first:
  1. the BM25 passages DPR retrieved for the question from all of Wikipedia (nq_build.py, answer removed);
  2. then BM25 over the ~600,000-passage pool (realdata/common.BM25) until the document is full.
Random passages: drawn from the pool, avoiding every article the look-alikes or the gold passage came from.
No passage that holds an answer, and no passage from the gold article, is ever used in a no-gold document.

Documents: passages in a random (seeded) order, each as "Title\\ntext", separated by blank lines.
In the control, the gold passage is placed between 35% and 65% of the document, as in NullScale.
Length is counted with the reference tokenizer (configs/experiments.yaml, Llama 3.1) and hit within 1%
by trimming the last passage at a word boundary.

Final checks on every finished document (a failure stops the script):
  no-gold documents contain no answer string and no passage of the gold article;
  the control contains the answer; every length is within the tolerance.

Output (paths.yaml data.nq; PC: ~/nullscale_work/data/nq/exp6/)
  questions.jsonl, docs/<doc_id>.txt, manifest.json      -> then run:  python -m run.run_vllm --exp exp6 ...
  outputs/realdata/exp6_build_report.md                   (project folder) checks, similarity, examples

Usage (Ubuntu/WSL, nullscale env, project folder; after nq_build.py; no GPU; 5-15 minutes)
  python -m realdata.retrieve
  python -m realdata.retrieve --limit 10           # quick try on 10 questions
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from realdata.common import BM25, OUT_DIR, holds_answer, read_jsonl_gz, write_jsonl  # noqa: E402
from realdata.nq_build import exp6_seed, nq_root  # noqa: E402

SEP = "\n\n"
DEFAULT_SETTINGS = ["gold_present_8k", "no_gold_lookalike_8k", "no_gold_random_8k",
                    "no_gold_lookalike_32k", "no_gold_random_32k"]
BM25_DEPTH = 3000


def parse_setting(name: str) -> dict:
    m = re.fullmatch(r"(gold_present|no_gold_lookalike|no_gold_random)_(\d+)k", name)
    if not m:
        raise SystemExit(f"setting not understood: {name}")
    kind, k = m.group(1), int(m.group(2))
    return {"name": name, "length_k": k, "gold": kind == "gold_present",
            "filler": "random" if kind.endswith("random") else "lookalike",
            "level": "gold" if kind == "gold_present" else ("random" if kind.endswith("random") else "lookalike")}


def load_settings():
    try:
        from nullscale.config import load_experiments
        e = load_experiments()
        d = e["defaults"]
        return (e["experiments"]["exp6"].get("settings") or DEFAULT_SETTINGS, int(d["length_unit_tokens"]),
                float(d["length_tolerance"]), d["reference_tokenizer"])
    except Exception:
        return DEFAULT_SETTINGS, 1000, 0.01, "meta-llama/Llama-3.1-8B-Instruct"


class Counter_:
    """Token counts with the reference tokenizer, cached per passage."""

    def __init__(self, name: str):
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(name)
        self.cache: dict[str, int] = {}
        self.sep = len(self.tok.encode(SEP, add_special_tokens=False))

    def n(self, text: str) -> int:
        return len(self.tok.encode(text, add_special_tokens=False))

    def passage(self, pid: str, text: str) -> int:
        if pid not in self.cache:
            self.cache[pid] = self.n(text)
        return self.cache[pid]

    def trim(self, text: str, n_tokens: int) -> str:
        """The first n_tokens of text, ending at a word boundary."""
        ids = self.tok.encode(text, add_special_tokens=False)[:max(0, n_tokens)]
        cut = self.tok.decode(ids)
        if " " in cut and len(cut) < len(text):
            cut = cut[:cut.rfind(" ")]
        return cut.rstrip()


def passage_text(p: dict) -> str:
    return f"{p['title']}\n{p['text']}"


def fill(order: list[dict], target: int, tol: float, tc: Counter_, gold: dict | None, rng: random.Random):
    """Choose passages from `order` (best first) until the document reaches target tokens.
    Returns (passages in document order, text, tokens, gold index)."""
    chosen, total = [], 0
    budget = target - (tc.passage(gold["docid"], passage_text(gold)) + tc.sep if gold else 0)
    for p in order:
        n = tc.passage(p["docid"], passage_text(p)) + tc.sep
        if total + n > budget:
            break
        chosen.append(dict(p))
        total += n
    rng.shuffle(chosen)
    gi = None
    if gold:
        gi = int(round(rng.uniform(0.35, 0.65) * len(chosen)))
        chosen.insert(gi, dict(gold, is_gold=True))
    # top up with a trimmed passage so the length lands inside the tolerance
    for _ in range(4):
        text = SEP.join(passage_text(p) for p in chosen)
        n = tc.n(text)
        if abs(n - target) <= tol * target:
            return chosen, text, n, gi
        if n < target:
            spare = next((p for p in order[len(chosen):] if not any(c["docid"] == p["docid"] for c in chosen)), None)
            if spare is None:
                break
            extra = tc.trim(spare["text"], target - n - tc.sep - tc.n(spare["title"]) - 2)
            if not extra:
                break
            chosen.append(dict(spare, text=extra, trimmed=True))
        else:   # too long: drop the last non-gold passage
            drop = max(i for i, p in enumerate(chosen) if not p.get("is_gold"))
            chosen.pop(drop)
    text = SEP.join(passage_text(p) for p in chosen)
    return chosen, text, tc.n(text), gi


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="NQ folder (default: paths.yaml data.nq)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions (quick try)")
    ap.add_argument("--tokenizer", help="reference tokenizer (default: experiments.yaml defaults.reference_tokenizer)")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else nq_root()
    settings, unit, tol, ref_tok = load_settings()
    settings = [parse_setting(s) for s in settings]
    seed = exp6_seed()
    qs = list(read_jsonl_gz(root / "nq300.jsonl")) if (root / "nq300.jsonl").exists() else sys.exit(
        f"{root / 'nq300.jsonl'} missing. Run: python -m realdata.nq_build")
    if a.limit:
        qs = qs[:a.limit]
    t0 = time.time()
    print("loading the passage pool ...")
    pool = list(read_jsonl_gz(root / "pool.jsonl.gz"))
    by_id = {p["docid"]: i for i, p in enumerate(pool)}
    print(f"  {len(pool):,} passages; building the BM25 index ...")
    bm25 = BM25((f"{p['title']} {p['text']}" for p in pool),
                progress=lambda i: print(f"    indexed {i:,}", flush=True))
    print(f"  index ready ({time.time() - t0:.0f}s); loading tokenizer {a.tokenizer or ref_tok}")
    tc = Counter_(a.tokenizer or ref_tok)

    out = root / "exp6"
    (out / "docs").mkdir(parents=True, exist_ok=True)
    rows, stats, examples = [], [], []
    for qi, q in enumerate(qs):
        rng = random.Random(seed * 1000 + q["idx"])
        answers, gold_titles = q["answers"], set(q["gold_titles"])

        def ok(p):
            return p["title"] not in gold_titles and not holds_answer(p["text"], answers, p["title"])

        # look-alikes: DPR's list first, then BM25 over the pool
        look, seen = [], set()
        for pid in q["similar_ids"]:
            if pid in by_id and pid not in seen:
                p = pool[by_id[pid]]
                if ok(p):
                    look.append(p)
                    seen.add(pid)
        for i, sc in bm25.top(q["question"], BM25_DEPTH):
            p = pool[i]
            if p["docid"] not in seen and ok(p):
                look.append(p)
                seen.add(p["docid"])
        look_titles = {p["title"] for p in look}
        # random: other articles only
        rand, tries = [], 0
        while len(rand) < 400 and tries < 20000:
            tries += 1
            p = pool[rng.randrange(len(pool))]
            if p["docid"] not in seen and p["title"] not in look_titles and ok(p):
                rand.append(p)
                seen.add(p["docid"])
        qscores = bm25.scores(q["question"])

        for s in settings:
            target = s["length_k"] * unit
            order = look if s["filler"] == "lookalike" else rand
            gold = q["gold_passage"] if s["gold"] else None
            chosen, text, n_tok, gi = fill(order, target, tol, tc, gold, rng)
            # final checks
            has = holds_answer(text, answers)
            if s["gold"] and not has:
                sys.exit(f"{q['nq_id']} {s['name']}: the control lost its answer")
            if not s["gold"] and (has or any(p["title"] in gold_titles for p in chosen)):
                sys.exit(f"{q['nq_id']} {s['name']}: answer found in a no-gold document (bug)")
            if abs(n_tok - target) > tol * target:
                sys.exit(f"{q['nq_id']} {s['name']}: {n_tok} tokens, target {target}")
            doc_id = f"nq{q['idx']:03d}-{s['name']}"
            (out / "docs" / f"{doc_id}.txt").write_text(text, encoding="utf-8")
            sims = [float(qscores[by_id[p["docid"]]]) for p in chosen if p["docid"] in by_id and not p.get("is_gold")]
            rows.append({
                "qid": f"{doc_id}/q0", "exp": "exp6", "doc_id": doc_id, "probe_id": "q0", "order": 0,
                "source": "wikipedia", "nq_id": q["nq_id"], "setting": s["name"],
                "question": q["question"], "answerable": s["gold"], "field": "nq_answer",
                "ladder": "nq", "level": s["level"], "copies": 0, "filler": s["filler"], "length_k": s["length_k"],
                "gold": answers[0] if s["gold"] else None, "gold_aliases": answers if s["gold"] else [],
                "true_answers": answers, "lookalike_values": [],
                "gold_position": round((gi + 0.5) / len(chosen), 3) if gi is not None else None,
                "n_passages": len(chosen), "n_tokens": n_tok, "mean_bm25_to_question": round(statistics.mean(sims), 3) if sims else None,
                "seed": seed, "doc_path": f"exp6/docs/{doc_id}.txt"})
            stats.append(rows[-1])
        if qi < 3:
            examples.append((q, [p["title"] for p in look[:5]], [p["title"] for p in rand[:5]]))
        if (qi + 1) % 25 == 0 or qi + 1 == len(qs):
            print(f"  {qi + 1}/{len(qs)} questions ({time.time() - t0:.0f}s)", flush=True)

    write_jsonl(out / "questions.jsonl", rows)
    manifest = {"exp": "exp6", "n_questions": len(qs), "n_documents": len(rows), "settings": [s["name"] for s in settings],
                "seed": seed, "reference_tokenizer": a.tokenizer or ref_tok, "pool_passages": len(pool),
                "bm25_depth": BM25_DEPTH, "built": time.strftime("%Y-%m-%d %H:%M")}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    L = ["# Exp 6 data, part 2: documents with look-alike or random Wikipedia passages", "",
         f"{len(qs)} questions x {len(settings)} settings = **{len(rows)} documents**, in `{out}`.", "",
         "Every no-gold document was checked: no answer string, no passage of the gold article. Every control "
         "document contains its answer. Every length is within 1% of its target.", "",
         "| setting | documents | tokens (mean) | passages (mean) | similarity to the question (mean BM25) | gold position (mean) |",
         "|---|---|---|---|---|---|"]
    for s in settings:
        rs = [r for r in stats if r["setting"] == s["name"]]
        sim = [r["mean_bm25_to_question"] for r in rs if r["mean_bm25_to_question"] is not None]
        gp = [r["gold_position"] for r in rs if r["gold_position"] is not None]
        L.append(f"| {s['name']} | {len(rs)} | {statistics.mean(r['n_tokens'] for r in rs):,.0f} | "
                 f"{statistics.mean(r['n_passages'] for r in rs):.0f} | {statistics.mean(sim):.2f} | "
                 f"{statistics.mean(gp):.2f} |" if gp else
                 f"| {s['name']} | {len(rs)} | {statistics.mean(r['n_tokens'] for r in rs):,.0f} | "
                 f"{statistics.mean(r['n_passages'] for r in rs):.0f} | {statistics.mean(sim) if sim else float('nan'):.2f} | - |")
    L += ["", "Look-alike documents should score clearly higher on similarity than random ones; that is the "
          "manipulation Exp 6 tests.", "", "## Examples", ""]
    for q, lt, rt in examples:
        L += [f"- **{q['question']}** (answer: {'; '.join(q['answers'][:2])}; gold article removed: {'; '.join(q['gold_titles'][:2])})",
              f"  - top look-alike articles: {'; '.join(lt)}", f"  - random articles: {'; '.join(rt)}"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "exp6_build_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nsaved {out / 'questions.jsonl'}, {len(rows)} documents, and {OUT_DIR / 'exp6_build_report.md'}")
    print("Next:  python -m run.run_vllm --model qwen3_4b --exp exp6 --n-docs 10 --balanced")


if __name__ == "__main__":
    main()
