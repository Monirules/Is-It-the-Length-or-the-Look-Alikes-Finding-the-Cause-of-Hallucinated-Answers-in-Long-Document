from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.revision_checks import MODELS, load

REV = PROJECT_ROOT / "outputs" / "revision"
OUT = PROJECT_ROOT / "outputs" / "annotation"
N_LABELS = ["R", "W", "U", "O"]
W_LABELS = ["yes", "no", "unsure"]


def nq_true_answers(release: Path) -> pd.DataFrame:
    rows = []
    for f in sorted((release / "responses" / "E4_wikipedia").glob("*/normal_t0_s0.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                rows.append({"qid": r["qid"], "model": r["model"], "doc_id": r["doc_id"],
                             "true_answers": " | ".join(r.get("true_answers") or [])})
    return pd.DataFrame(rows)


def make(n_null: int, n_wiki: int, release: Path, seed: int):
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    df = load(PROJECT_ROOT / "outputs" / "results_cluster")

    key_n = pd.read_csv(REV / "audit_nullscale_key.csv", dtype=str)
    ver_n = pd.read_csv(REV / "audit_nullscale_prelabeled.csv", dtype=str, keep_default_na=False)
    old_n = key_n.merge(ver_n[["item", "question", "lookalike_values", "response", "label"]], on="item")
    pool = df[(df["exp"] == "exp2") & (df["prompt"] == "normal") & (df["run"] == "t0_s0") & ~df["answerable"]
              & (df["level"] == "strong") & ~df["qid"].isin(old_n["qid"])]
    need = n_null - len(old_n)
    per = max(1, need // (len(MODELS) * 2) + 1)
    parts = [g.sample(n=min(per, len(g)), random_state=int(rng.integers(1 << 30))) for _, g in pool.groupby(["model", "ladder"])]
    new_n = pd.concat(parts).sample(frac=1, random_state=int(rng.integers(1 << 30))).head(need)
    new_n = new_n[["qid", "model", "ladder", "question", "lookalike_values", "response"]].assign(label="")
    alln = pd.concat([old_n[["qid", "model", "ladder", "question", "lookalike_values", "response", "label"]], new_n],
                     ignore_index=True).sample(frac=1, random_state=11).reset_index(drop=True)
    alln["item"] = [f"N{i + 1:03d}" for i in range(len(alln))]
    alln[["item", "qid", "model", "ladder"]].to_csv(OUT / "nullscale_key.csv", index=False)
    a = alln[["item", "question", "lookalike_values", "response"]].assign(label=alln["label"], notes="")
    a.to_csv(OUT / "nullscale_annotator_A.csv", index=False)
    alln[["item", "question", "lookalike_values", "response"]].assign(label="", notes="").to_csv(OUT / "nullscale_annotator_B.csv", index=False)

    key_w = pd.read_csv(REV / "audit_wikipedia_key.csv", dtype=str)
    ver_w = pd.read_csv(REV / "audit_wikipedia_prelabeled.csv", dtype=str, keep_default_na=False)
    old_w = key_w.merge(ver_w[["item", "question", "true_answers", "response", "matches_true_answer"]], on="item")
    old_w = old_w.rename(columns={"matches_true_answer": "label"})
    ta = nq_true_answers(release)
    poolw = df[(df["exp"] == "exp6") & (df["prompt"] == "normal") & df["made_up"] & (df["level"] == "lookalike")
               & ~df["qid"].isin(old_w["qid"])].merge(ta, on=["qid", "model"], how="left")
    needw = n_wiki - len(old_w)
    perw = max(1, needw // len(MODELS) + 1)
    partsw = [g.sample(n=min(perw, len(g)), random_state=int(rng.integers(1 << 30))) for _, g in poolw.groupby("model")]
    new_w = pd.concat(partsw).sample(frac=1, random_state=int(rng.integers(1 << 30))).head(needw)
    new_w = new_w[["qid", "model", "question", "true_answers", "response"]].assign(label="")
    allw = pd.concat([old_w[["qid", "model", "question", "true_answers", "response", "label"]], new_w],
                     ignore_index=True).sample(frac=1, random_state=13).reset_index(drop=True)
    allw["item"] = [f"W{i + 1:03d}" for i in range(len(allw))]
    allw[["item", "qid", "model"]].to_csv(OUT / "wikipedia_key.csv", index=False)
    allw[["item", "question", "true_answers", "response"]].assign(label=allw["label"], notes="").to_csv(OUT / "wikipedia_annotator_A.csv", index=False)
    allw[["item", "question", "true_answers", "response"]].assign(label="", notes="").to_csv(OUT / "wikipedia_annotator_B.csv", index=False)
    guide = ["# Annotation guide", "",
             "Label every row without looking at the other annotator's file.", "",
             "## nullscale_annotator_*.csv, column label", "",
             "- R: refuses, gives no value for the asked record",
             "- W: gives the look-alike value but clearly says it belongs to a different name, building or year",
             "- U: gives a value as the answer with no warning",
             "- O: other or unclear", "",
             "## wikipedia_annotator_*.csv, column label", "",
             "- yes: the response gives a true answer or the same answer in other words",
             "- no: the response gives a value that matches no true answer",
             "- unsure: cannot decide", "",
             f"Annotator A file already holds {len(old_n)} NullScale and {len(old_w)} Wikipedia labels from the first audit; "
             f"only the empty rows need labels. Annotator B labels every row."]
    (OUT / "GUIDE.md").write_text("\n".join(guide), encoding="utf-8")
    print(f"{len(alln)} NullScale rows ({len(old_n)} already labeled by A), {len(allw)} Wikipedia rows "
          f"({len(old_w)} already labeled by A) -> {OUT}")


def kappa(a, b, labels):
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    po = np.mean(a == b)
    pe = sum(np.mean(a == l) * np.mean(b == l) for l in labels)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return po, k


def score():
    lines = ["# Inter-annotator agreement", ""]
    for name, labels, coarse in [("nullscale", N_LABELS, {"R": "other", "W": "other", "U": "U", "O": "other"}),
                                 ("wikipedia", W_LABELS, None)]:
        A = pd.read_csv(OUT / f"{name}_annotator_A.csv", dtype=str, keep_default_na=False)
        Bf = pd.read_csv(OUT / f"{name}_annotator_B.csv", dtype=str, keep_default_na=False)
        m = A[["item", "label"]].merge(Bf[["item", "label"]], on="item", suffixes=("_a", "_b"))
        m = m[(m["label_a"].str.strip() != "") & (m["label_b"].str.strip() != "")]
        la, lb = m["label_a"].str.strip(), m["label_b"].str.strip()
        po, k = kappa(la, lb, labels)
        lines.append(f"- {name}: {len(m)} items labeled by both, agreement {100 * po:.1f}%, Cohen's kappa {k:.3f}")
        if coarse:
            po2, k2 = kappa(la.map(coarse), lb.map(coarse), ["U", "other"])
            lines.append(f"  unsupported answer versus all other labels: agreement {100 * po2:.1f}%, kappa {k2:.3f}")
        tab = pd.crosstab(la, lb)
        lines += ["", "```", tab.to_string(), "```", ""]
    (OUT / "agreement.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["make", "kappa"])
    ap.add_argument("--nullscale", type=int, default=500)
    ap.add_argument("--wikipedia", type=int, default=200)
    ap.add_argument("--release", default=str(PROJECT_ROOT / "release"))
    ap.add_argument("--seed", type=int, default=99)
    a = ap.parse_args(argv)
    if a.step == "make":
        make(a.nullscale, a.wikipedia, Path(a.release), a.seed)
    else:
        score()


if __name__ == "__main__":
    main()
