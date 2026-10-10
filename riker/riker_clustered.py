from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.review2_checks import logit_fit
from riker.common import OUT_DIR, iter_cache, riker_root
from riker.reanalyze_riker import load_lookalikes

CTX = (32, 128, 200)


def collect(root: Path, la: dict, level: str):
    cells = defaultdict(lambda: [0, 0])
    for r in iter_cache(root, levels=(level,)):
        if r["failed"]:
            continue
        q = la.get((r["context_k"], r["question_id"]))
        if q is None:
            continue
        c = cells[(r["model"], r["context_k"], r["question_id"], bool(q["present"]))]
        c[0] += not r["riker_correct"]
        c[1] += 1
    d = pd.DataFrame([{"model": m, "ctx": k, "qid": q, "present": p, "made_up": v[0], "n": v[1]}
                      for (m, k, q, p), v in cells.items()])
    full = d.groupby("model")["ctx"].nunique()
    panel = sorted(full[full == len(CTX)].index)
    return d[d["model"].isin(panel)].reset_index(drop=True), panel


def design(d: pd.DataFrame, models: list[str]):
    lam = np.log2(d["ctx"].to_numpy() / 32)
    pr = d["present"].to_numpy().astype(float)
    cols = [np.ones(len(d)), pr, lam, pr * lam] + [(d["model"] == m).to_numpy().astype(float) for m in models[1:]]
    X1 = np.column_stack(cols)
    X = np.vstack([X1, X1])
    y = np.concatenate([np.ones(len(d)), np.zeros(len(d))])
    w = np.concatenate([d["made_up"].to_numpy(), (d["n"] - d["made_up"]).to_numpy()]).astype(float)
    qid = np.tile((d["ctx"].astype(str) + "/" + d["qid"]).to_numpy(), 2)
    mod = np.tile(d["model"].to_numpy(), 2)
    cell = np.tile(np.arange(len(d)), 2)
    return X, y, w, qid, mod, cell


def question_bootstrap(d: pd.DataFrame, models: list[str], B: int, rng):
    keys = (d["ctx"].astype(str) + "/" + d["qid"]).to_numpy()
    by_ctx = {k: np.unique(keys[d["ctx"].to_numpy() == k]) for k in CTX}
    idx = {k: np.where(keys == k)[0] for k in np.unique(keys)}
    out = []
    for _ in range(B):
        rows = []
        for k in CTX:
            pick = rng.choice(by_ctx[k], size=len(by_ctx[k]), replace=True)
            rows += [i for q in pick for i in idx[q]]
        X, y, w, *_ = design(d.iloc[rows].reset_index(drop=True), models)
        b, _, _ = logit_fit(X, y, w, ridge=1e-6)
        out.append(b[1:4])
    return np.array(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--level", default="L12")
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "review2"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(a.root) if a.root else riker_root()
    la = load_lookalikes(OUT_DIR / "lookalikes.csv")
    d, panel = collect(root, la, a.level)
    if d.empty:
        sys.exit("no RIKER2 answers found; check --root")
    X, y, w, qid, mod, cell = design(d, panel)
    terms = ["look-alike present at 32K", "log2(length/32K) without look-alike", "present x log2(length/32K)"]
    res = []
    for name, groups in [("naive (answers independent)", None), ("clustered by question", qid),
                         ("clustered by model", mod), ("two-way: question and model", [qid, mod, cell])]:
        b, se, _ = logit_fit(X, y, w, groups=groups, ridge=1e-6)
        for i, t in enumerate(terms, start=1):
            res.append({"errors": name, "term": t, "log_odds": b[i], "se": se[i], "z": b[i] / se[i] if se[i] else math.nan})
    rng = np.random.default_rng(7)
    bs = question_bootstrap(d, panel, a.boot, rng)
    for i, t in enumerate(terms):
        res.append({"errors": f"question bootstrap ({a.boot} draws)", "term": t, "log_odds": float(np.mean(bs[:, i])),
                    "se": float(np.std(bs[:, i], ddof=1)), "z": float(np.mean(bs[:, i]) / np.std(bs[:, i], ddof=1)),
                    "lo": float(np.percentile(bs[:, i], 2.5)), "hi": float(np.percentile(bs[:, i], 97.5))})
    r = pd.DataFrame(res)
    r.to_csv(out / "F_riker_clustered.csv", index=False)
    info = {"level": a.level, "models": panel, "n_models": len(panel), "questions": int(d.groupby(["ctx", "qid"]).ngroups),
            "answers": int(d["n"].sum())}
    (out / "F_riker_clustered_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(json.dumps(info))
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
