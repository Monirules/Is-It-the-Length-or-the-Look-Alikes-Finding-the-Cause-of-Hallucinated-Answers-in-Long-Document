from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.revision_checks import (MODELS, NAMES, ci, doc_arrays, fmt, load, rate_row,
                                      unpaired_diff)

LENGTHS = [8, 32, 64, 128]
B = 2000


def logit_fit(X, y, w, groups=None, ridge=0.1, iters=100):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    w = np.asarray(w, float)
    p = X.shape[1]
    P = np.eye(p) * ridge
    P[0, 0] = 0.0
    b = np.zeros(p)
    for _ in range(iters):
        eta = X @ b
        mu = 1 / (1 + np.exp(-eta))
        W = w * mu * (1 - mu)
        H = X.T @ (W[:, None] * X) + P
        g = X.T @ (w * (y - mu)) - P @ b
        step = np.linalg.solve(H, g)
        b += step
        if np.max(np.abs(step)) < 1e-8:
            break
    eta = X @ b
    mu = 1 / (1 + np.exp(-eta))
    W = w * mu * (1 - mu)
    Hinv = np.linalg.inv(X.T @ (W[:, None] * X) + P)
    if groups is None:
        return b, np.sqrt(np.diag(Hinv)), Hinv
    S = (w * (y - mu))[:, None] * X
    covs = []
    for gr in (groups if isinstance(groups, list) else [groups]):
        gr = np.asarray(gr)
        U = pd.DataFrame(S).groupby(gr).sum().to_numpy()
        G = len(U)
        covs.append(Hinv @ (U.T @ U) @ Hinv * G / max(G - 1, 1))
    V = covs[0] if len(covs) == 1 else covs[0] + covs[1] - covs[2]
    V = (V + V.T) / 2
    return b, np.sqrt(np.clip(np.diag(V), 0, None)), V


def dersimonian_laird(est, se):
    est, se = np.asarray(est, float), np.asarray(se, float)
    w = 1 / se ** 2
    fixed = np.sum(w * est) / np.sum(w)
    q = np.sum(w * (est - fixed) ** 2)
    k = len(est)
    tau2 = max(0.0, (q - (k - 1)) / (np.sum(w) - np.sum(w ** 2) / np.sum(w)))
    wr = 1 / (se ** 2 + tau2)
    mu = np.sum(wr * est) / np.sum(wr)
    se_mu = math.sqrt(1 / np.sum(wr))
    return mu, se_mu, tau2, q


def per_model_effects(df, rng):
    d0 = df[(df["exp"] == "exp3") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]]
    rows = []
    for m in MODELS:
        for fil in ["pooled", "unrelated", "sibling"]:
            d = d0[d0["model"] == m]
            if fil != "pooled":
                d = d[d["filler"] == fil]
            Ls = [L for L in LENGTHS if not d[d["length"] == L].empty]
            longest = max(Ls)
            cell = lambda lv, L: d[(d["level"] == lv) & (d["length"] == L)]
            r = {"model": NAMES[m], "filler": fil, "longest": f"{longest}K"}
            for name, a, b in [("lookalike_8k", cell("strong", 8), cell("none", 8)),
                               ("lookalike_32k", cell("strong", 32), cell("none", 32)),
                               ("lookalike_longest", cell("strong", longest), cell("none", longest)),
                               ("length_none", cell("none", longest), cell("none", 8)),
                               ("length_strong", cell("strong", longest), cell("strong", 8))]:
                dd = unpaired_diff(a, b, "made_up", rng, perms=2000)
                r[name], r[name + "_lo"], r[name + "_hi"], r[name + "_p"] = dd["diff"], dd["diff_lo"], dd["diff_hi"], dd["p_doc_perm"]
            ka = [doc_arrays(cell(lv, L), "made_up") for lv, L in [("strong", longest), ("none", longest), ("strong", 8), ("none", 8)]]
            draws = []
            for _ in range(B):
                vals = []
                for k, n, _ in ka:
                    idx = rng.integers(0, len(n), len(n))
                    vals.append(k[idx].sum() / max(n[idx].sum(), 1))
                draws.append((vals[0] - vals[1]) - (vals[2] - vals[3]))
            draws = np.array(draws)
            obs = (r["lookalike_longest"] - r["lookalike_8k"])
            lo, hi = ci(draws)
            r["interaction"], r["interaction_lo"], r["interaction_hi"] = obs, 100 * lo, 100 * hi
            rows.append(r)
    return pd.DataFrame(rows)


def two_stage_mixed(df):
    d0 = df[(df["exp"] == "exp3") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]].copy()
    d0["lam"] = np.log2(d0["length"] / 8)
    d0["s"] = (d0["level"] == "strong").astype(float)
    d0["r"] = (d0["ladder"] == "role").astype(float)
    d0["f"] = (d0["filler"] == "sibling").astype(float)
    terms = ["beta_length_no_lookalike", "beta_strong_at_8k", "beta_length_x_strong", "beta_length_additive", "beta_strong_additive"]
    rows = []
    for m in MODELS:
        d = d0[d0["model"] == m]
        y = d["made_up"].astype(float).to_numpy()
        w = np.ones(len(d))
        X_int = np.column_stack([np.ones(len(d)), d["lam"], d["s"], d["lam"] * d["s"], d["r"], d["f"]])
        b, se, _ = logit_fit(X_int, y, w, groups=d["doc"].to_numpy())
        X_add = np.column_stack([np.ones(len(d)), d["lam"], d["s"], d["r"], d["f"]])
        b2, se2, _ = logit_fit(X_add, y, w, groups=d["doc"].to_numpy())
        rows.append({"model": NAMES[m], "beta_length_no_lookalike": b[1], "se_length_no_lookalike": se[1],
                     "beta_strong_at_8k": b[2], "se_strong_at_8k": se[2],
                     "beta_length_x_strong": b[3], "se_length_x_strong": se[3],
                     "beta_length_additive": b2[1], "se_length_additive": se2[1],
                     "beta_strong_additive": b2[2], "se_strong_additive": se2[2],
                     "n": len(d), "documents": d["doc"].nunique()})
    pm = pd.DataFrame(rows)
    pooled = []
    for t in terms:
        key = t.replace("beta_", "")
        mu, se_mu, tau2, q = dersimonian_laird(pm[t], pm["se_" + key])
        pooled.append({"term": t, "pooled": mu, "se": se_mu, "lo": mu - 1.96 * se_mu, "hi": mu + 1.96 * se_mu,
                       "between_model_sd": math.sqrt(tau2), "Q": q,
                       "prediction_lo": mu - 1.96 * math.sqrt(se_mu ** 2 + tau2),
                       "prediction_hi": mu + 1.96 * math.sqrt(se_mu ** 2 + tau2)})
    pooled = pd.DataFrame(pooled)
    rng = np.random.default_rng(1)
    ps = pooled.set_index("term")
    s_draw = rng.normal(ps.loc["beta_strong_at_8k", "pooled"], math.sqrt(ps.loc["beta_strong_at_8k", "se"] ** 2 + ps.loc["beta_strong_at_8k", "between_model_sd"] ** 2), 20000)
    l_draw = rng.normal(ps.loc["beta_length_no_lookalike", "pooled"], math.sqrt(ps.loc["beta_length_no_lookalike", "se"] ** 2 + ps.loc["beta_length_no_lookalike", "between_model_sd"] ** 2), 20000)
    ratio = s_draw / l_draw
    exch = {"exchange_rate_point": ps.loc["beta_strong_at_8k", "pooled"] / ps.loc["beta_length_no_lookalike", "pooled"],
            "share_draws_slope_not_positive": float(np.mean(l_draw <= 0)),
            "ratio_p2_5": float(np.percentile(ratio, 2.5)), "ratio_p97_5": float(np.percentile(ratio, 97.5))}
    return pm, pooled, exch


def riker_near_matches(riker_dir: Path):
    f = riker_dir / "lookalikes.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f, dtype=str, keep_default_na=False)
    d = d[d["parse_ok"] == "True"].copy()
    d["n_lookalikes"] = pd.to_numeric(d["n_lookalikes"], errors="coerce").fillna(0)
    d["n_partial"] = pd.to_numeric(d["n_partial"], errors="coerce").fillna(0)
    d["context_k"] = d["context_k"].astype(int)
    rows = []
    for (L, lev), g in d.groupby(["context_k", "level"]):
        rows.append({"length": L, "level": lev, "questions": len(g),
                     "share_with_lookalike": 100 * (g["lookalike_present"] == "True").mean(),
                     "mean_lookalikes": g["n_lookalikes"].mean(), "median_lookalikes": g["n_lookalikes"].median(),
                     "share_two_or_more": 100 * (g["n_lookalikes"] >= 2).mean(),
                     "mean_partial_matches": g["n_partial"].mean(),
                     "mean_lookalikes_plus_partial": (g["n_lookalikes"] + g["n_partial"]).mean()})
    for L, g in d.groupby("context_k"):
        rows.append({"length": L, "level": "all", "questions": len(g),
                     "share_with_lookalike": 100 * (g["lookalike_present"] == "True").mean(),
                     "mean_lookalikes": g["n_lookalikes"].mean(), "median_lookalikes": g["n_lookalikes"].median(),
                     "share_two_or_more": 100 * (g["n_lookalikes"] >= 2).mean(),
                     "mean_partial_matches": g["n_partial"].mean(),
                     "mean_lookalikes_plus_partial": (g["n_lookalikes"] + g["n_partial"]).mean()})
    return pd.DataFrame(rows).sort_values(["level", "length"])


def heuristic_fit(df):
    d0 = df[(df["exp"] == "exp3") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]]
    grid_q = np.concatenate([[0.0], np.logspace(-7, -1, 3000)])
    grid_s = np.linspace(0.001, 0.999, 999)
    rows = []
    for m in MODELS:
        d = d0[d0["model"] == m]
        none = {L: (d[(d["level"] == "none") & (d["length"] == L)]["made_up"].sum(), (d[(d["level"] == "none") & (d["length"] == L)]).shape[0]) for L in LENGTHS}
        strong = {L: (d[(d["level"] == "strong") & (d["length"] == L)]["made_up"].sum(), (d[(d["level"] == "strong") & (d["length"] == L)]).shape[0]) for L in LENGTHS}
        Ls = [L for L in LENGTHS if none[L][1] > 0]
        best = (-1e18, 0.0, 0.5)
        for q in grid_q:
            ll0 = 0.0
            for L in Ls:
                k, n = none[L]
                f = 1 - (1 - q) ** L
                f = min(max(f, 1e-9), 1 - 1e-9)
                ll0 += k * math.log(f) + (n - k) * math.log(1 - f)
            for s in grid_s[::10]:
                ll = ll0
                for L in Ls:
                    k, n = strong[L]
                    f = 1 - (1 - s) * (1 - q) ** L
                    f = min(max(f, 1e-9), 1 - 1e-9)
                    ll += k * math.log(f) + (n - k) * math.log(1 - f)
                if ll > best[0]:
                    best = (ll, q, s)
        _, q, s = best
        pred = {L: 100 * (1 - (1 - q) ** L) for L in [8, 16, 32, 64, 96, 112, 128]}
        obs = {L: 100 * none[L][0] / none[L][1] for L in Ls}
        r = {"model": NAMES[m], "p0_per_1k_tokens": q, "p_s": s}
        for L in [8, 16, 32, 64, 96, 112, 128]:
            r[f"pred_none_{L}k"] = pred[L]
            if L in obs:
                r[f"obs_none_{L}k"] = obs[L]
        lo8 = 100 * none[8][0] / max(none[8][1], 1)
        r["pred_break_16k"] = pred[16] - lo8 > 2.0
        r["pred_break_96k"] = pred[96] - lo8 > 2.0
        rows.append(r)
    return pd.DataFrame(rows)


def exp8_control(df, scores: Path | None, rng):
    d0 = df[(df["exp"] == "exp8") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]]
    if d0.empty:
        return None, None
    rows = []
    for m in MODELS:
        for ladder in ["both", "name", "role"]:
            d = d0[d0["model"] == m]
            if d.empty:
                continue
            if ladder != "both":
                d = d[d["ladder"] == ladder]
            r = {"model": NAMES[m], "ladder": ladder}
            for lv in ["none", "decoy", "strong"]:
                rr = rate_row(d[d["level"] == lv], "made_up", rng)
                r[lv], r[lv + "_lo"], r[lv + "_hi"], r[lv + "_docs"] = rr["rate"], rr["boot_lo"], rr["boot_hi"], rr["docs"]
            for name, a, b in [("decoy_minus_none", "decoy", "none"), ("strong_minus_decoy", "strong", "decoy")]:
                dd = unpaired_diff(d[d["level"] == a], d[d["level"] == b], "made_up", rng)
                r[name], r[name + "_lo"], r[name + "_hi"], r[name + "_p"] = dd["diff"], dd["diff_lo"], dd["diff_hi"], dd["p_doc_perm"]
            rows.append(r)
    cap = None
    if scores and scores.exists():
        crow = []
        for m in MODELS:
            f = scores / "exp8" / m / "normal_t0_s0.scored.jsonl"
            if not f.exists():
                continue
            opener = gzip.open if f.suffix == ".gz" else open
            n_mu = n_dec = 0
            with opener(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    if r.get("level") != "decoy" or r.get("answerable") or r.get("label") != "made_up":
                        continue
                    n_mu += 1
                    resp = (r.get("answer_part") or r.get("response") or "").lower().replace(",", "")
                    if any(v and v.lower().replace(",", "") in resp for v in (r.get("decoy_values") or [])):
                        n_dec += 1
            crow.append({"model": NAMES[m], "made_up_in_decoy": n_mu, "copied_decoy_value": n_dec,
                         "share": 100 * n_dec / n_mu if n_mu else math.nan})
        cap = pd.DataFrame(crow)
    return pd.DataFrame(rows), cap


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results_cluster"))
    ap.add_argument("--riker", default=str(PROJECT_ROOT / "outputs" / "riker"))
    ap.add_argument("--scores", default=None)
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "review2"))
    ap.add_argument("--seed", type=int, default=2028)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    df = load(Path(a.results))

    pe = per_model_effects(df, rng)
    pe.to_csv(out / "A_per_model_effects.csv", index=False)
    pm, pooled, exch = two_stage_mixed(df)
    pm.to_csv(out / "B_per_model_logit.csv", index=False)
    pooled.to_csv(out / "B_random_effects_pooled.csv", index=False)
    (out / "B_exchange_rate.json").write_text(json.dumps(exch, indent=1), encoding="utf-8")
    nm = riker_near_matches(Path(a.riker))
    if nm is not None:
        nm.to_csv(out / "C_riker_near_matches.csv", index=False)
    hf = heuristic_fit(df)
    hf.to_csv(out / "D_heuristic_predictions.csv", index=False)
    e8, cap = exp8_control(df, Path(a.scores) if a.scores else None, rng)
    if e8 is not None:
        e8.to_csv(out / "E_exp8_control.csv", index=False)
    if cap is not None:
        cap.to_csv(out / "E_exp8_decoy_capture.csv", index=False)

    R = ["# Review 2 checks", "",
         "All intervals resample whole documents (2,000 draws). Unpaired tests are document permutation tests.", "",
         "## A. Per model effects in Experiment 2 (points)", "",
         "lookalike_X = strong minus none at length X. length_none = none at the longest length minus none at 8K. "
         "interaction = lookalike_longest minus lookalike_8k (negative means the look-alike effect shrinks with length).", "",
         fmt(pe[["model", "filler", "longest", "lookalike_8k", "lookalike_8k_lo", "lookalike_8k_hi",
                 "lookalike_longest", "lookalike_longest_lo", "lookalike_longest_hi",
                 "length_none", "length_none_lo", "length_none_hi", "length_none_p",
                 "interaction", "interaction_lo", "interaction_hi"]]), "",
         "## B. Two stage mixed model (per model logistic fits with document clustered errors, pooled by DerSimonian and Laird random effects)", "",
         fmt(pm, digits=3), "", fmt(pooled, digits=3), "",
         f"Exchange rate from pooled terms: {exch['exchange_rate_point']:.2f} doublings. "
         f"Across models the length slope without a look-alike is not positive in {100 * exch['share_draws_slope_not_positive']:.0f}% of draws from the random effects distribution, "
         f"and the ratio ranges from {exch['ratio_p2_5']:.1f} to {exch['ratio_p97_5']:.1f} (2.5 and 97.5 percentiles), so the exchange rate is not identified across models.", ""]
    if nm is not None:
        R += ["## C. RIKER2 near matches per trap question", "", fmt(nm, digits=2), ""]
    R += ["## D. Heuristic model fit and predictions (no look-alike fabrication, %)", "",
          "p0 is the per 1K token chance of a wrong accept, p_s the chance for the strong look-alike. Predictions at 16K, 96K and 112K are made before any run.", "",
          fmt(hf, digits=3), ""]
    if e8 is not None:
        R += ["## E. Experiment 8 control: same eight extra records, none matching the asked key", "", fmt(e8), ""]
        if cap is not None:
            R += ["Share of made up answers in decoy documents that copy a decoy value:", "", fmt(cap), ""]
    else:
        R += ["## E. Experiment 8 control", "", "No exp8 results found yet.", ""]
    (out / "report.md").write_text("\n".join(R), encoding="utf-8")
    print("\n".join(R))


if __name__ == "__main__":
    main()
