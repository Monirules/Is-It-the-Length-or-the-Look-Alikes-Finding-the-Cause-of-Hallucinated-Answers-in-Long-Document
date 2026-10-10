from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STOP = {"the", "a", "an", "of", "in", "on", "at", "to", "and", "is", "was", "for", "by", "it", "its", "as", "with", "from", "that"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(w for w in s.split() if w not in STOP)


def years(s: str) -> set[str]:
    return set(re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(s)))


def numbers(s: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", str(s).replace(",", "")))


def label(row) -> tuple[str, str, str]:
    resp = str(row["response"])
    rn = f" {norm(resp)} "
    answers = [t for t in str(row["true_answers"]).split(" | ") if t.strip()]
    for t in answers:
        tn = norm(t)
        if tn and f" {tn} " in rn:
            return "yes", f"true answer '{t}' appears in the reply (answered from memory)", "high"
    for t in answers:
        ty, ry = years(t), years(resp)
        if ty and ty & ry:
            return "yes", f"same year as true answer '{t}'", "medium"
        tnum, rnum = numbers(t) - ty, numbers(resp) - ry
        if tnum and tnum <= rnum:
            return "yes", f"same number as true answer '{t}'", "medium"
    for t in answers:
        tw, rw = set(norm(t).split()), set(rn.split())
        if tw and len(tw & rw) / len(tw) >= 0.5:
            return "unsure", f"partial word overlap with true answer '{t}'", "low"
    return "no", "reply does not match any true answer", "medium"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_wikipedia_sheet.csv"))
    ap.add_argument("--context", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_wikipedia_context.csv"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "revision" / "audit_wikipedia_prelabeled.csv"))
    a = ap.parse_args(argv)
    s = pd.read_csv(a.sheet, dtype=str, keep_default_na=False)
    lab = s.apply(label, axis=1, result_type="expand")
    s["matches_true_answer"], s["reason"], s["confidence"] = lab[0], lab[1], lab[2]
    c = Path(a.context)
    if c.exists():
        ctx = pd.read_csv(c, dtype=str, keep_default_na=False)[["item", "true_answer_in_context"]]
        s = s.merge(ctx, on="item", how="left")
    else:
        s["true_answer_in_context"] = ""
    s["answer_in_passages"] = s["true_answer_in_context"].map(lambda v: "yes" if v == "True" else "no")
    s["verified"] = ""
    s = s[["item", "question", "true_answers", "response", "answer_in_passages", "matches_true_answer",
           "confidence", "reason", "verified", "notes"]]
    s.to_csv(a.out, index=False)
    print(s["answer_in_passages"].value_counts().to_string())
    print(s["matches_true_answer"].value_counts().to_string())
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
