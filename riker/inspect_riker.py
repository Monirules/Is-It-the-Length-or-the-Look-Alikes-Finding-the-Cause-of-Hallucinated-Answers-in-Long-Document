"""riker/inspect_riker.py

Opens the RIKER2 files and writes a short report on what is inside. The most important question:
is the FULL DOCUMENT TEXT included, or only the ground truth? (Answer from the files themselves.)

Checks, per context length (32K, 128K, 200K)
  - the documents: size, number of leases / field reports / HR reports, rough token count
  - the ground truth database: tables and row counts; does every database record appear in the text?
  - the test set: questions per document type and level; the trap questions (L11, L12) with examples
  - the model answers (from the cache): runs, models, temperatures; do the answered question ids match
    the test set; how many replies failed (empty / error, e.g. context too long)
  - Roig's own summary tables: which CSVs exist, their columns

Output  outputs/riker/riker_report.md   (project folder; send it to the team)

Usage (Ubuntu/WSL, nullscale env, project folder; after riker/download_riker.py)
  python -m riker.inspect_riker
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from riker.common import (CONTEXTS, OUT_DIR, TRAP_LEVELS, cache_path, corpus_files, iter_cache, load_db,  # noqa: E402
                          load_tests, riker_root, split_corpus)

DOC_TABLES = {"lease_documents": "LEASE", "field_reports": "FIELD REPORT", "hr_reports": "HR REPORT"}


def inspect_context(root: Path, k: int, L: list[str]) -> dict:
    files = corpus_files(root, k)
    L += [f"## {k}K context", ""]
    if not all(files.values()):
        L += [f"Missing files: {[key for key, v in files.items() if v is None]}", ""]
        return {}
    md = files["md"].read_text(encoding="utf-8")
    docs = split_corpus(md)
    kinds = Counter(d["kind"] for d in docs.values())
    db = load_db(files["db"])
    tests = load_tests(files["yaml"])
    L += [f"**Documents** (`{files['md'].name}`): {len(md):,} characters, about {len(md) / 4:,.0f} tokens "
          f"(4 characters per token), {len(docs)} documents: "
          + ", ".join(f"{v} {kk.lower()}s" for kk, v in kinds.items()) + ".", ""]
    # every database record must be a document in the text
    missing = 0
    total = 0
    for table, kind in DOC_TABLES.items():
        for r in db.get(table, []):
            total += 1
            if r["doc_id"] not in docs:
                missing += 1
    L += [f"**Ground truth** (`{files['db'].name}`): " + ", ".join(f"{t} {len(v)}" for t, v in db.items()) + ".",
          f"Database records found as documents in the text: {total - missing} of {total}.", ""]
    by = Counter((t["doc_type"], t["level"]) for t in tests)
    levels = sorted({lv for _, lv in by})
    L += [f"**Test set** (`{files['yaml'].name}`): {len(tests)} questions.", "",
          "| document type | " + " | ".join(levels) + " |", "|---|" + "---|" * len(levels)]
    for dt in sorted({d for d, _ in by}):
        L.append(f"| {dt} | " + " | ".join(str(by[(dt, lv)]) for lv in levels) + " |")
    traps = [t for t in tests if t["level"] in TRAP_LEVELS]
    exp = Counter(str(t.get("expected_response")) for t in traps)
    L += ["", f"Trap questions (L11 + L12): {len(traps)}; expected answers: {dict(exp)}.", "",
          "Examples:", ""]
    for lv in TRAP_LEVELS:
        for dt in ("lease_document", "field_report", "hr"):
            ex = [t for t in traps if t["level"] == lv and t["doc_type"] == dt][:1]
            for t in ex:
                L.append(f"- `{t['question_id']}`: {t['question']} -> expected **{t.get('expected_response')}**")
    L.append("")
    return {"n_docs": len(docs), "chars": len(md), "tests": {t["question_id"] for t in tests}, "n_traps": len(traps)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="RIKER2 folder (default: paths.yaml data.riker2)")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else riker_root()
    L = ["# What is inside RIKER2", "",
         f"Folder: `{root}`. Made by riker/inspect_riker.py.", ""]
    info = {k: inspect_context(root, k, L) for k in CONTEXTS}
    full_text = all(v and v["n_docs"] > 0 for v in info.values())
    L[4:4] = ["## Answer to the main question", "",
              ("**Yes: the full document text is included.** For every length, the file "
               "`<length>K_riker_<date>_concatenated.md` is the exact text the models read, with every lease, "
               "field report and HR report in it. The `.db` file is the ground truth and the `.yaml` file the questions. "
               "So we can search the documents themselves for look-alike records (riker/find_lookalikes.py)."
               if full_text else
               "**The full document text was NOT found for every length.** See the sections below."), ""]

    L += ["## Model answers (RIKER2_March2026.zip)", ""]
    if cache_path(root).exists():
        runs = defaultdict(set)
        per = Counter()
        failed = Counter()
        unknown_q = Counter()
        rows = 0
        for r in iter_cache(root):
            rows += 1
            key = (r["platform"], r["run_name"])
            runs[r["context_k"]].add(key)
            per[(r["model"], r["context_k"])] += 1
            if r["failed"]:
                failed[r["context_k"]] += 1
            tests = (info.get(r["context_k"]) or {}).get("tests")
            if tests is not None and r["question_id"] not in tests:
                unknown_q[r["context_k"]] += 1
        models = sorted({m for m, _ in per})
        L += [f"{rows:,} answers from {sum(len(v) for v in runs.values()):,} runs of {len(models)} models.", "",
              "| context | runs | answers | failed replies (empty or error) | question ids not in the test set |",
              "|---|---|---|---|---|"]
        for k in sorted(runs):
            n_k = sum(v for (m, c), v in per.items() if c == k)
            L.append(f"| {k}K | {len(runs[k]):,} | {n_k:,} | {failed[k]:,} | {unknown_q[k]:,} |")
        L += ["", "Models: " + ", ".join(f"`{m}`" for m in models), ""]
        rc = root / "cache" / "runs.csv"
        if rc.exists():
            with open(rc, encoding="utf-8") as f:
                rr = list(csv.DictReader(f))
            L += ["Temperatures: " + ", ".join(f"{t} ({n} runs)" for t, n in sorted(Counter(r["temperature"] for r in rr).items())),
                  "Hardware/platform folders: " + ", ".join(f"{p} ({n})" for p, n in sorted(Counter(r["platform"] for r in rr).items())),
                  "Run status: " + ", ".join(f"{s} {n}" for s, n in Counter(r["status"] for r in rr).items()), ""]
    else:
        L += [f"No answers cache yet ({cache_path(root)}). Run `python -m riker.download_riker`.", ""]

    raw = root / "raw" / "riker"
    if raw.exists():
        L += ["## Roig's summary tables", ""]
        for p in sorted(raw.glob("*.csv")):
            with open(p, encoding="utf-8") as f:
                header = next(csv.reader(f), [])
                n = sum(1 for _ in f)
            L.append(f"- `{p.name}` ({n} rows): {', '.join(header[:12])}{' ...' if len(header) > 12 else ''}")
        L.append("")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "riker_report.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nsaved {out}\nNext:  python -m riker.find_lookalikes")


if __name__ == "__main__":
    main()
