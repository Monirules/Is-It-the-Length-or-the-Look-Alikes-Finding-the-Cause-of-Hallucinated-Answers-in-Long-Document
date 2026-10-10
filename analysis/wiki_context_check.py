from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(the|a|an)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def find(doc_n: str, doc_raw: str, answer: str, width: int = 160):
    a = norm(answer)
    if len(a) < 2 or f" {a} " not in f" {doc_n} ":
        return None
    first = answer.split()[0] if answer.split() else answer
    i = doc_raw.lower().find(first.lower())
    if i < 0:
        return "found after normalisation"
    return doc_raw[max(0, i - width): i + len(answer) + width].replace("\n", " ")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_wikipedia_sheet.csv"))
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_wikipedia_context.csv"))
    a = ap.parse_args(argv)
    if a.data:
        root = Path(a.data)
    else:
        from nullscale.config import load_paths
        root = Path(load_paths()["data"]["nq"])
    docs = root / "exp6" / "docs" if (root / "exp6" / "docs").exists() else root / "docs"
    sheet = pd.read_csv(a.sheet, dtype=str, keep_default_na=False)
    rows = []
    for r in sheet.itertuples(index=False):
        p = docs / f"{r.doc_id}.txt"
        if not p.exists():
            rows.append({"item": r.item, "doc_found": False})
            continue
        raw = p.read_text(encoding="utf-8")
        dn = norm(raw)
        hits = [(t, find(dn, raw, t)) for t in r.true_answers.split(" | ") if t.strip()]
        hits = [(t, s) for t, s in hits if s]
        rows.append({"item": r.item, "doc_found": True, "true_answer_in_context": bool(hits),
                     "matched_answer": hits[0][0] if hits else "", "snippet": hits[0][1] if hits else ""})
    out = pd.DataFrame(rows)
    out.to_csv(a.out, index=False)
    n = int(out.get("true_answer_in_context", pd.Series(dtype=bool)).fillna(False).sum())
    print(f"{len(out)} items, {int(out['doc_found'].sum())} documents found, {n} with a true answer string in the context -> {a.out}")


if __name__ == "__main__":
    main()
