"""nullscale/build_dataset.py

Builds every NullScale document and question for the experiments in configs/experiments.yaml,
proves absence for each document, and saves the final dataset.

  exp2, exp3, exp4   the full grid (lengths x ladders x levels x copies x filler x contexts_per_cell)
  exp5               25 documents at 32K with strong look-alikes (200 + 100 questions); the
                     retrieval pool of 5,000 records for the fixes is built later, in fixes/
  exp7               20 documents at 32K with strong look-alikes
  exp1, exp6         not NullScale (RIKER2 and Natural Questions) -> skipped

For every document: build -> absence_check -> if it fails, rebuild with a new seed (up to 5 tries)
-> save. A document that still fails stops the run with an error, so nothing unproven is saved.

Output (in <paths.data.nullscale>, i.e. ~/nullscale_work/data/nullscale on the PC):
  <exp>/docs/<doc_id>.txt     the document text the model reads
  <exp>/docs/<doc_id>.json    records, spans, look-alike positions, questions (ground truth)
  <exp>/questions.jsonl       one line per question (12 per document)
  <exp>/manifest.json         counts, tokenizer, rebuilds, length deviations, config snapshot

Usage (Ubuntu, nullscale env, project folder; no GPU needed):
  python -m nullscale.build_dataset --exp exp2 --limit 4     # quick try: 4 documents
  python -m nullscale.build_dataset --exp all                # everything (exp2, 3, 4, 5, 7)
  python -m nullscale.build_dataset --exp exp3 --lengths 8,32 --workers 6
Existing documents are reused (skipped) unless --overwrite is given.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from itertools import product
from multiprocessing import get_context
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from nullscale.absence_check import check_document, load_document  # noqa: E402
from nullscale.assemble import DocSpec, build_document, load_tokenizer  # noqa: E402
from nullscale.config import load_experiments, load_paths  # noqa: E402

NULLSCALE_TYPES = ("nullscale", "fixes", "batching")
MAX_TRIES = 5


# ----------------------------------------------------------------------------- specs

def experiment_specs(name: str, exp: dict, defaults: dict) -> list[DocSpec]:
    base = defaults["base_seed"] + exp.get("seed_offset", 0) * 1000
    unit, tol = defaults["length_unit_tokens"], defaults["length_tolerance"]
    specs = []
    if exp["type"] == "nullscale":
        grid = product(exp["lengths"], exp["ladders"], exp["lookalike_levels"],
                       exp["lookalike_copies"], exp["filler"])
        k = 0
        for L, ladder, level, copies, filler in grid:
            for _ in range(exp["contexts_per_cell"]):
                specs.append(DocSpec(L, ladder, level, filler, copies, base + k, unit=unit, tolerance=tol))
                k += 1
    elif exp["type"] in ("fixes", "batching"):
        for k in range(exp["contexts"]):
            ladder = exp["ladders"][k % len(exp["ladders"])]
            specs.append(DocSpec(exp["lengths"][0], ladder, exp["lookalike_levels"][0], exp["filler"][0],
                                 exp["lookalike_copies"][0], base + k, unit=unit, tolerance=tol))
    return specs


# ----------------------------------------------------------------------------- worker

def _build_one(args):
    spec, out_dir, overwrite = args
    json_path = Path(out_dir) / f"{spec.doc_id}.json"
    if json_path.exists() and not overwrite:
        doc = load_document(json_path)
        return {"doc_id": spec.doc_id, "reused": True, "tries": 0, "questions": doc["questions"],
                "deviation": doc["deviation"], "n_tokens": doc["n_tokens"], "failed": check_document(doc)}
    tok = load_tokenizer()
    tried = []
    for attempt in range(MAX_TRIES):
        s = spec if attempt == 0 else DocSpec(**{**spec.__dict__, "seed": spec.seed + 7919 * attempt})
        doc = build_document(s, tok)
        problems = check_document(doc) if doc["within_tolerance"] else ["length outside tolerance"]
        if not problems:
            doc["doc_id"] = spec.doc_id                  # keep the planned id even after a rebuild
            doc["rebuild_seed"] = s.seed if attempt else None
            for q in doc["questions"]:
                q["doc_id"] = spec.doc_id
                q["qid"] = f"{spec.doc_id}/{q['probe_id']}"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.with_suffix(".txt").write_text(doc["text"], encoding="utf-8")
            json_path.write_text(json.dumps({k: v for k, v in doc.items() if k != "text"}, separators=(",", ":")),
                                 encoding="utf-8")
            return {"doc_id": spec.doc_id, "reused": False, "tries": attempt + 1, "questions": doc["questions"],
                    "deviation": doc["deviation"], "n_tokens": doc["n_tokens"], "failed": [],
                    "tokenizer": doc["tokenizer"]}
        tried.append(problems[:2])
    return {"doc_id": spec.doc_id, "reused": False, "tries": MAX_TRIES, "questions": [],
            "deviation": None, "n_tokens": None, "failed": tried}


# ----------------------------------------------------------------------------- main

def build_experiment(name: str, exp: dict, defaults: dict, root: Path, workers: int,
                     limit: int | None, lengths: set[int] | None, overwrite: bool) -> dict:
    specs = experiment_specs(name, exp, defaults)
    if lengths:
        specs = [s for s in specs if s.length_k in lengths]
    if limit:
        specs = specs[:limit]
    out_dir = root / name / "docs"
    print(f"\n=== {name}: {exp['title']}  ({len(specs)} documents) ===")
    t0 = time.time()
    jobs = [(s, str(out_dir), overwrite) for s in specs]
    results = []
    if workers > 1:
        with get_context("fork").Pool(workers) as pool:
            for i, r in enumerate(pool.imap(_build_one, jobs, chunksize=1), 1):
                results.append(r)
                _progress(i, len(jobs), t0)
    else:
        for i, j in enumerate(jobs, 1):
            results.append(_build_one(j))
            _progress(i, len(jobs), t0)
    print()

    bad = [r for r in results if r["failed"]]
    if bad:
        for r in bad[:5]:
            print(f"  FAILED {r['doc_id']}: {r['failed']}")
        sys.exit(f"{len(bad)} document(s) in {name} could not be proven absent after {MAX_TRIES} tries")

    qpath = root / name / "questions.jsonl"
    with open(qpath, "w", encoding="utf-8") as f:
        for r, s in zip(results, specs):
            for q in sorted(r["questions"], key=lambda q: q["order"]):
                row = {"exp": name, **q, "length_k": s.length_k, "ladder": s.ladder, "level": s.level,
                       "copies": s.copies, "filler": s.filler, "seed": s.seed,
                       "doc_path": f"{name}/docs/{s.doc_id}.txt"}
                f.write(json.dumps(row) + "\n")

    devs = [r["deviation"] for r in results]
    n_q = sum(len(r["questions"]) for r in results)
    manifest = {
        "exp": name, "title": exp["title"], "n_documents": len(results), "n_questions": n_q,
        "n_unanswerable": sum(not q["answerable"] for r in results for q in r["questions"]),
        "n_answerable": sum(q["answerable"] for r in results for q in r["questions"]),
        "tokenizer": next((r.get("tokenizer") for r in results if r.get("tokenizer")), "reused"),
        "rebuilt_documents": sum(r["tries"] > 1 for r in results),
        "reused_documents": sum(r["reused"] for r in results),
        "deviation_min": min(devs) if devs else None, "deviation_max": max(devs) if devs else None,
        "partial": bool(limit or lengths),
        "config": exp, "defaults": defaults,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (root / name / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"  documents {manifest['n_documents']}  questions {n_q} "
          f"({manifest['n_unanswerable']} no answer + {manifest['n_answerable']} with answer)  "
          f"rebuilt {manifest['rebuilt_documents']}  reused {manifest['reused_documents']}  "
          f"length deviation {min(devs):+.2%} .. {max(devs):+.2%}  [{time.time() - t0:.0f}s]")
    print(f"  saved: {qpath}")
    return manifest


def _progress(i, n, t0):
    if i == n or i % max(1, n // 20) == 0:
        el = time.time() - t0
        print(f"\r  {i}/{n} documents  {el:.0f}s elapsed, ~{el / i * (n - i):.0f}s left   ", end="", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exp", default="all", help="all, or a comma list like exp2,exp3")
    ap.add_argument("--limit", type=int, default=None, help="only the first N documents per experiment")
    ap.add_argument("--lengths", default=None, help="only these lengths, e.g. 8,32")
    ap.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 2) - 1)))
    ap.add_argument("--out", default=None, help="output root (default: paths.yaml data.nullscale)")
    ap.add_argument("--overwrite", action="store_true", help="rebuild documents that already exist")
    a = ap.parse_args()

    ecfg = load_experiments()
    defaults, exps = ecfg["defaults"], ecfg["experiments"]
    root = Path(a.out) if a.out else Path(load_paths()["data"]["nullscale"])
    names = [n for n, e in exps.items() if e["type"] in NULLSCALE_TYPES] if a.exp == "all" else a.exp.split(",")
    lengths = {int(x) for x in a.lengths.split(",")} if a.lengths else None

    tok = load_tokenizer()          # load once here so the workers inherit it
    print(f"tokenizer: {tok.name}   output: {root}   workers: {a.workers}")
    if tok.name == "approx-regex":
        print("WARNING: approximate token counts. Real runs need the Llama tokenizer (hf auth login).")
    for n in names:
        if n not in exps:
            sys.exit(f"unknown experiment {n}")
        if exps[n]["type"] not in NULLSCALE_TYPES:
            print(f"\n=== {n}: skipped ({exps[n]['type']} data is not generated by NullScale) ===")
            continue
        build_experiment(n, exps[n], defaults, root, a.workers, a.limit, lengths, a.overwrite)
    print("\nDone.")


if __name__ == "__main__":
    main()
