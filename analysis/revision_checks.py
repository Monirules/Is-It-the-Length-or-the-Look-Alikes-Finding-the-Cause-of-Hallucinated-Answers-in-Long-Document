from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

MODELS = ["qwen3_4b", "llama31_8b", "gemma3_27b", "qwen3_30b_a3b", "llama33_70b", "qwen3_next_80b", "glm45_air"]
NAMES = {"qwen3_4b": "Qwen3 4B", "llama31_8b": "Llama 3.1 8B", "gemma3_27b": "Gemma 3 27B",
         "qwen3_30b_a3b": "Qwen3 30B A3B", "llama33_70b": "Llama 3.3 70B", "qwen3_next_80b": "Qwen3 Next 80B",
         "glm45_air": "GLM 4.5 Air 106B"}
PAPER_EXP = {"exp2": "Exp 1", "exp3": "Exp 2", "exp4": "Exp 3", "exp6": "Exp 4", "exp7": "Exp 5"}
LEVELS = ["none", "weak", "medium", "strong"]
LENGTHS = [8, 32, 64, 128]
FLAG_RX = re.compile(r"\b(however|note|noting|although|though|but|closest|similar|instead|not exactly|"
                     r"spelled|spelling|typo|differ|different|assum|might|may be|possibly|likely|seems|appears)\b", re.I)
B = 2000


def load(results: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(results.glob("*/scored.csv")):
        name = f.parent.name
        exp = name.split("_")[0]
        rest = name[len(exp) + 1:]
        prompt = next((p for p in ("normal", "strict", "batch12") if f"_{p}_" in rest), None)
        if prompt is None:
            continue
        model, run = rest.split(f"_{prompt}_")
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        d["exp"], d["model"], d["prompt"], d["run"] = exp, model, prompt, run
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["answerable"] = df["answerable"] == "True"
    df["made_up"] = df["label"] == "made_up"
    df["answered"] = df["label"].isin(["correct", "wrong"])
    df["correct"] = df["label"] == "correct"
    df["scorable"] = df["label"] != "other"
    df["length"] = df["length_k"].astype(int)
    df["copies_n"] = pd.to_numeric(df["copies"], errors="coerce").fillna(0).astype(int)
    df["doc"] = df["qid"].str.split("/").str[0]
    df["flagged"] = df["made_up"] & ((df["hedged"] == "True") | df["response"].str.contains(FLAG_RX))
    return df


def wilson(k, n, z=1.96):
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def doc_arrays(d: pd.DataFrame, col: str):
    g = d.groupby("doc")[col].agg(["sum", "count"])
    return g["sum"].to_numpy(float), g["count"].to_numpy(float), g.index.to_numpy()


def boot_rate(k, n, rng, b=B):
    if len(n) == 0:
        return np.full(b, np.nan)
    w = rng.multinomial(len(n), np.full(len(n), 1 / len(n)), size=b)
    return (w @ k) / np.maximum(w @ n, 1)


def ci(a):
    a = a[~np.isnan(a)]
    if len(a) == 0:
        return (math.nan, math.nan)
    return (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)))


def rate_row(d: pd.DataFrame, col: str, rng):
    k, n, _ = doc_arrays(d, col)
    tot_k, tot_n = k.sum(), n.sum()
    p = tot_k / tot_n if tot_n else math.nan
    bl, bh = ci(boot_rate(k, n, rng))
    wl, wh = wilson(tot_k, tot_n)
    return {"k": int(tot_k), "n": int(tot_n), "docs": len(n), "rate": 100 * p,
            "wilson_lo": 100 * wl, "wilson_hi": 100 * wh, "boot_lo": 100 * bl, "boot_hi": 100 * bh}


def unpaired_diff(a: pd.DataFrame, b: pd.DataFrame, col: str, rng, perms=5000):
    ka, na, _ = doc_arrays(a, col)
    kb, nb, _ = doc_arrays(b, col)
    da = boot_rate(ka, na, rng) - boot_rate(kb, nb, rng)
    obs = ka.sum() / na.sum() - kb.sum() / nb.sum()
    k = np.concatenate([ka, kb])
    n = np.concatenate([na, nb])
    m = len(ka)
    hits = 0
    for _ in range(perms):
        idx = rng.permutation(len(k))
        x, y = idx[:m], idx[m:]
        if abs(k[x].sum() / n[x].sum() - k[y].sum() / n[y].sum()) >= abs(obs) - 1e-12:
            hits += 1
    lo, hi = ci(da)
    return {"diff": 100 * obs, "diff_lo": 100 * lo, "diff_hi": 100 * hi, "p_doc_perm": (hits + 1) / (perms + 1)}


def mcnemar_exact(b01, b10):
    from scipy.stats import binomtest
    n = b01 + b10
    return 1.0 if n == 0 else float(binomtest(b01, n, 0.5).pvalue)


def paired_diff(a: pd.DataFrame, b: pd.DataFrame, col: str, rng):
    m = a[["qid", "doc", col]].merge(b[["qid", col]], on="qid", suffixes=("_a", "_b"))
    g = m.groupby("doc").agg(ka=(f"{col}_a", "sum"), kb=(f"{col}_b", "sum"), n=("qid", "count"))
    ka, kb, n = (g[c].to_numpy(float) for c in ("ka", "kb", "n"))
    w = rng.multinomial(len(n), np.full(len(n), 1 / len(n)), size=B)
    da = (w @ ka - w @ kb) / (w @ n)
    lo, hi = ci(da)
    b01 = int(((m[f"{col}_a"]) & (~m[f"{col}_b"])).sum())
    b10 = int(((~m[f"{col}_a"]) & (m[f"{col}_b"])).sum())
    return {"n": len(m), "docs": len(n), "rate_a": 100 * ka.sum() / n.sum(), "rate_b": 100 * kb.sum() / n.sum(),
            "diff": 100 * (ka.sum() - kb.sum()) / n.sum(), "diff_lo": 100 * lo, "diff_hi": 100 * hi,
            "a_only": b01, "b_only": b10, "p_mcnemar": mcnemar_exact(b01, b10)}


def holm(ps):
    order = np.argsort(ps)
    out = np.empty(len(ps))
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i]))
        out[i] = run
    return out


def z(p):
    from scipy.stats import norm
    return norm.ppf(min(max(p, 0.005), 0.995))


def sample_sizes(df):
    rows = []
    for (exp, model, prompt, run), d in df.groupby(["exp", "model", "prompt", "run"]):
        rows.append({"experiment": PAPER_EXP.get(exp, exp), "code": exp, "model": model, "prompt": prompt, "run": run,
                     "answers": len(d), "documents": d["doc"].nunique(),
                     "unanswerable": int((~d["answerable"]).sum()), "answerable": int(d["answerable"].sum())})
    ss = pd.DataFrame(rows)
    cells = []
    main = df[(df["prompt"] == "normal") & (df["run"] == "t0_s0") & df["model"].isin(MODELS)]
    for (exp, model), d in main.groupby(["exp", "model"]):
        u = d[~d["answerable"]]
        keys = {"exp2": ["level"], "exp3": ["level", "length"], "exp4": ["copies_n"], "exp6": ["level", "length"],
                "exp7": ["level"]}.get(exp, ["level"])
        for key, c in u.groupby(keys):
            key = key if isinstance(key, tuple) else (key,)
            cells.append({"experiment": PAPER_EXP.get(exp, exp), "model": model,
                          "cell": "/".join(str(x) for x in key), "unanswerable": len(c), "documents": c["doc"].nunique()})
    return ss, pd.DataFrame(cells)


def exp1(df, rng):
    d0 = df[(df["exp"] == "exp2") & (df["prompt"] == "normal") & (df["run"] == "t0_s0") & ~df["answerable"]]
    rows, diffs = [], []
    for m in MODELS:
        for ladder in ["both", "name", "role"]:
            d = d0[d0["model"] == m]
            if ladder != "both":
                d = d[d["ladder"] == ladder]
            for lv in LEVELS:
                rows.append({"model": NAMES[m], "ladder": ladder, "level": lv, **rate_row(d[d["level"] == lv], "made_up", rng)})
            diffs.append({"model": NAMES[m], "ladder": ladder,
                          **unpaired_diff(d[d["level"] == "strong"], d[d["level"] == "none"], "made_up", rng)})
    return pd.DataFrame(rows), pd.DataFrame(diffs)


def exp2(df, rng):
    d0 = df[(df["exp"] == "exp3") & (df["prompt"] == "normal") & df["model"].isin(MODELS)]
    rows = []
    for m in MODELS:
        for fil in ["pooled", "unrelated", "sibling"]:
            d = d0[d0["model"] == m]
            if fil != "pooled":
                d = d[d["filler"] == fil]
            for L in LENGTHS:
                dl = d[d["length"] == L]
                if dl.empty:
                    continue
                for lv in ["none", "strong"]:
                    u = dl[(~dl["answerable"]) & (dl["level"] == lv)]
                    rows.append({"model": NAMES[m], "filler": fil, "length": L, "measure": f"made_up_{lv}",
                                 **rate_row(u, "made_up", rng)})
                a = dl[dl["answerable"]]
                rows.append({"model": NAMES[m], "filler": fil, "length": L, "measure": "accuracy",
                             **rate_row(a, "correct", rng)})
    return pd.DataFrame(rows)


def breaking(e2):
    out = []
    for m in MODELS:
        d = e2[(e2["model"] == NAMES[m]) & (e2["filler"] == "pooled") & (e2["measure"] == "made_up_none")].set_index("length")
        r = {"model": NAMES[m]}
        for kind, lo, hi in [("wilson", "wilson_lo", "wilson_hi"), ("doc_bootstrap", "boot_lo", "boot_hi")]:
            r[kind] = next((f"{L}K" for L in LENGTHS[1:] if L in d.index and d.loc[L, lo] > d.loc[8, hi]), "none")
        out.append(r)
    return pd.DataFrame(out)


def same_filler(df, rng):
    d0 = df[(df["exp"] == "exp3") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]]
    rows = []
    for m in MODELS:
        dm = d0[d0["model"] == m]
        for fil in ["unrelated", "sibling"]:
            d = dm[dm["filler"] == fil]
            longest = max(L for L in LENGTHS if not d[d["length"] == L].empty)
            cell = lambda lv, L: d[(d["level"] == lv) & (d["length"] == L)]
            s32, nlong, n8, s8, slong = cell("strong", 32), cell("none", longest), cell("none", 8), cell("strong", 8), cell("strong", longest)
            r = {"model": NAMES[m], "filler": fil, "longest": f"{longest}K"}
            for name, x in [("strong_32k", s32), ("none_longest", nlong), ("none_8k", n8), ("strong_8k", s8)]:
                rr = rate_row(x, "made_up", rng)
                r[name] = rr["rate"]
                r[name + "_lo"], r[name + "_hi"] = rr["boot_lo"], rr["boot_hi"]
                r[name + "_docs"] = rr["docs"]
            for name, a, b in [("gap_strong32_vs_none_longest", s32, nlong),
                               ("lookalike_effect_8k", s8, n8),
                               ("lookalike_effect_longest", slong, nlong),
                               ("length_effect_none", nlong, n8)]:
                dd = unpaired_diff(a, b, "made_up", rng, perms=2000)
                r[name], r[name + "_lo"], r[name + "_hi"], r[name + "_p"] = dd["diff"], dd["diff_lo"], dd["diff_hi"], dd["p_doc_perm"]
            rows.append(r)
    return pd.DataFrame(rows)


def exp3(df, rng):
    d0 = df[(df["exp"] == "exp4") & (df["prompt"] == "normal") & df["model"].isin(MODELS) & ~df["answerable"]]
    rows = []
    for m in MODELS:
        d = d0[d0["model"] == m]
        r = {"model": NAMES[m]}
        for c in [1, 2, 4, 8]:
            rr = rate_row(d[d["copies_n"] == c], "made_up", rng)
            r[f"c{c}"], r[f"c{c}_lo"], r[f"c{c}_hi"], r[f"c{c}_docs"] = rr["rate"], rr["boot_lo"], rr["boot_hi"], rr["docs"]
        dd = unpaired_diff(d[d["copies_n"] == 8], d[d["copies_n"] == 1], "made_up", rng)
        r.update({"diff_8_minus_1": dd["diff"], "diff_lo": dd["diff_lo"], "diff_hi": dd["diff_hi"], "p_doc_perm": dd["p_doc_perm"]})
        rows.append(r)
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p_doc_perm"].to_numpy())
    return out


def exp4(df, rng):
    d0 = df[(df["exp"] == "exp6") & (df["prompt"] == "normal") & df["model"].isin(MODELS)]
    rows = []
    for m in MODELS:
        d = d0[d0["model"] == m]
        for lv in ["lookalike", "random"]:
            for L in [8, 32]:
                rows.append({"model": NAMES[m], "passages": "similar" if lv == "lookalike" else lv, "length": L,
                             **rate_row(d[(~d["answerable"]) & (d["level"] == lv) & (d["length"] == L)], "made_up", rng)})
        rows.append({"model": NAMES[m], "passages": "gold present", "length": 8,
                     **rate_row(d[d["answerable"]], "correct", rng)})
    return pd.DataFrame(rows)


def paired(df, rng):
    rows = []
    base = df[df["prompt"] == "normal"]
    for m in ["qwen3_4b", "llama31_8b"]:
        a = df[(df["exp"] == "exp7") & (df["model"] == m) & (df["prompt"] == "batch12") & ~df["answerable"]]
        b = base[(base["exp"] == "exp7") & (base["model"] == m) & ~base["answerable"]]
        rows.append({"comparison": "Exp 5: 12 per call minus 1 per call, made up", "model": NAMES[m], **paired_diff(a, b, "made_up", rng)})
        a = df[(df["exp"] == "exp7") & (df["model"] == m) & (df["prompt"] == "batch12") & df["answerable"]]
        b = base[(base["exp"] == "exp7") & (base["model"] == m) & base["answerable"]]
        rows.append({"comparison": "Exp 5: 12 per call minus 1 per call, accuracy", "model": NAMES[m], **paired_diff(a, b, "correct", rng)})
    fp8 = base[(base["exp"] == "exp3") & (base["model"] == "llama33_70b") & (base["length"] == 128)]
    bf16 = base[(base["exp"] == "exp3") & (base["model"] == "llama33_70b_bf16")]
    for lv in ["none", "strong"]:
        rows.append({"comparison": f"Llama 3.3 70B 128K: FP8 minus bf16, made up, {lv}", "model": NAMES["llama33_70b"],
                     **paired_diff(fp8[(~fp8["answerable"]) & (fp8["level"] == lv)], bf16[(~bf16["answerable"]) & (bf16["level"] == lv)], "made_up", rng)})
    rows.append({"comparison": "Llama 3.3 70B 128K: FP8 minus bf16, accuracy", "model": NAMES["llama33_70b"],
                 **paired_diff(fp8[fp8["answerable"]], bf16[bf16["answerable"]], "correct", rng)})
    for m in MODELS:
        st = df[(df["exp"] == "exp2") & (df["model"] == m) & (df["prompt"] == "strict")]
        if st.empty:
            continue
        nm = base[(base["exp"] == "exp2") & (base["model"] == m) & (base["run"] == "t0_s0")]
        rows.append({"comparison": "Strict minus normal prompt, made up (strong, 32K)", "model": NAMES[m],
                     **paired_diff(st[~st["answerable"]], nm[~nm["answerable"]], "made_up", rng)})
        rows.append({"comparison": "Strict minus normal prompt, accuracy (strong, 32K)", "model": NAMES[m],
                     **paired_diff(st[st["answerable"]], nm[nm["answerable"]], "correct", rng)})
    for m in MODELS:
        nm = base[(base["exp"] == "exp2") & (base["model"] == m) & (base["run"] == "t0_s0") & ~base["answerable"] & (base["level"] == "strong")]
        for s in ["t0.7_s1", "t0.7_s2", "t0.7_s3"]:
            t7 = base[(base["exp"] == "exp2") & (base["model"] == m) & (base["run"] == s) & ~base["answerable"] & (base["level"] == "strong")]
            if not t7.empty:
                rows.append({"comparison": f"T=0.7 {s[-2:]} minus T=0, made up (strong, 32K)", "model": NAMES[m],
                             **paired_diff(t7, nm, "made_up", rng)})
    return pd.DataFrame(rows)


def sdt_stats(d):
    ans = d[d["answerable"] & d["scorable"]]
    un = d[(~d["answerable"]) & (d["level"] == "strong") & d["scorable"]]
    H = ans["answered"].mean()
    F = un["made_up"].mean()
    return H, F, z(H) - z(F), -(z(H) + z(F)) / 2, ans.loc[ans["answered"], "correct"].mean()


def sdt_boot(d, rng):
    docs = d["doc"].unique()
    groups = {k: g for k, g in d.groupby("doc")}
    H, F, dp, c, prec = sdt_stats(d)
    res = []
    for _ in range(1000):
        pick = rng.choice(docs, size=len(docs), replace=True)
        res.append(sdt_stats(pd.concat([groups[p] for p in pick], ignore_index=True))[2:4])
    res = np.array(res)
    return {"answer_rate_answerable": 100 * H, "answer_rate_unanswerable": 100 * F, "d_prime": dp,
            "d_lo": ci(res[:, 0])[0], "d_hi": ci(res[:, 0])[1], "c": c, "c_lo": ci(res[:, 1])[0], "c_hi": ci(res[:, 1])[1],
            "correct_given_answered": 100 * prec}


def sdt(df, rng):
    rows = []
    base = df[df["prompt"] == "normal"]
    for m in MODELS:
        d = base[(base["exp"] == "exp3") & (base["model"] == m) & (base["level"] == "strong")]
        for fil in ["unrelated", "sibling"]:
            rows.append({"condition": f"Exp 2, {fil} filler", "model": NAMES[m], **sdt_boot(d[d["filler"] == fil], rng)})
        st = df[(df["exp"] == "exp2") & (df["model"] == m) & (df["prompt"] == "strict")]
        if not st.empty:
            nm = base[(base["exp"] == "exp2") & (base["model"] == m) & (base["run"] == "t0_s0") & base["doc"].isin(st["doc"].unique())]
            rows.append({"condition": "Exp 1 strong, normal prompt", "model": NAMES[m], **sdt_boot(nm, rng)})
            rows.append({"condition": "Exp 1 strong, strict prompt", "model": NAMES[m], **sdt_boot(st, rng)})
    return pd.DataFrame(rows)


def three_way(df):
    d0 = df[(df["exp"] == "exp2") & (df["prompt"] == "normal") & (df["run"] == "t0_s0") & ~df["answerable"]]
    rows = []
    for m in MODELS:
        for ladder in ["name", "role"]:
            d = d0[(d0["model"] == m) & (d0["ladder"] == ladder)]
            s, n = d[d["level"] == "strong"], d[d["level"] == "none"]
            silent = lambda x: (x["made_up"] & ~x["flagged"]).mean() * 100
            rows.append({"model": NAMES[m], "ladder": ladder, "n_strong": len(s),
                         "refused": 100 * (s["label"] == "refused").mean(), "made_up_flagged": 100 * s["flagged"].mean(),
                         "made_up_silent": silent(s), "effect_all": 100 * (s["made_up"].mean() - n["made_up"].mean()),
                         "effect_silent_only": silent(s) - silent(n)})
    return pd.DataFrame(rows)


def audit_nullscale(df, out: Path, rng):
    d0 = df[(df["exp"] == "exp2") & (df["prompt"] == "normal") & (df["run"] == "t0_s0") & ~df["answerable"]
            & (df["level"] == "strong") & (df["label"].isin(["made_up", "refused"]))]
    parts = []
    for (m, ladder), g in d0.groupby(["model", "ladder"]):
        mu = g[g["made_up"]]
        parts.append(mu.sample(n=min(12, len(mu)), random_state=int(rng.integers(1 << 30))))
        rf = g[~g["made_up"]]
        parts.append(rf.sample(n=min(3, len(rf)), random_state=int(rng.integers(1 << 30))))
    s = pd.concat(parts).sample(frac=1, random_state=7).reset_index(drop=True)
    s["item"] = [f"N{i + 1:03d}" for i in range(len(s))]
    sheet = s[["item", "question", "lookalike_values", "response"]].copy()
    sheet["label"] = ""
    sheet["notes"] = ""
    key = s[["item", "qid", "model", "ladder", "label", "flagged", "captured"]].rename(columns={"label": "auto_label", "flagged": "auto_flag"})
    sheet.to_csv(out / "audit_nullscale_sheet.csv", index=False)
    key.to_csv(out / "audit_nullscale_key.csv", index=False)
    return len(s)


def audit_wikipedia(release: Path, df, out: Path, rng):
    rows = []
    for f in sorted((release / "responses" / "E4_wikipedia").glob("*/normal_t0_s0.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                rows.append({"qid": r["qid"], "model": r["model"], "doc_id": r["doc_id"], "setting": r.get("setting"),
                             "true_answers": " | ".join(r.get("true_answers") or [])})
    if not rows:
        return 0
    meta = pd.DataFrame(rows)
    d = df[(df["exp"] == "exp6") & (df["prompt"] == "normal") & df["made_up"] & (df["level"] == "lookalike")]
    d = d.merge(meta, on=["qid", "model"], how="left")
    parts = [g.sample(n=min(15, len(g)), random_state=int(rng.integers(1 << 30))) for _, g in d.groupby("model")]
    s = pd.concat(parts).sample(frac=1, random_state=11).reset_index(drop=True)
    s["item"] = [f"W{i + 1:03d}" for i in range(len(s))]
    sheet = s[["item", "doc_id", "question", "true_answers", "response"]].copy()
    sheet["answer_in_passages"] = ""
    sheet["notes"] = ""
    sheet.to_csv(out / "audit_wikipedia_sheet.csv", index=False)
    s[["item", "qid", "model", "setting", "source"]].to_csv(out / "audit_wikipedia_key.csv", index=False)
    return len(s)


def fig_same_filler(sf: pd.DataFrame, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "x", "grid.color": "#e5e7eb"})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    names = [NAMES[m] for m in MODELS]
    y = np.arange(len(names))[::-1]
    series = [("lookalike_effect_8k", "Look-alike effect at 8K", "#c2410c"),
              ("lookalike_effect_longest", "Look-alike effect at longest length", "#f59e0b"),
              ("length_effect_none", "Length effect, 8K to longest, no look-alike", "#64748b")]
    for ax, fil in zip(axes, ["unrelated", "sibling"]):
        d = sf[sf["filler"] == fil].set_index("model").loc[names]
        for j, (col, lab, colr) in enumerate(series):
            v = d[col].to_numpy()
            err = np.vstack([v - d[col + "_lo"].to_numpy(), d[col + "_hi"].to_numpy() - v])
            ax.barh(y + (1 - j) * 0.26, v, 0.26, xerr=err, color=colr, label=lab,
                    error_kw=dict(lw=0.7, capsize=1.5, ecolor="#334155"))
        ax.axvline(0, color="#334155", lw=0.8)
        ax.set_title(f"{fil.capitalize()} filler", fontsize=9.5, loc="left", fontweight="bold")
        ax.set_xlabel("Change in made up answers (points)")
        ax.set_xlim(-10, 100)
    axes[0].set_yticks(y, names)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out / "fig_same_filler.pdf", bbox_inches="tight")
    fig.savefig(out / "fig_same_filler.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fmt(df, cols=None, digits=1):
    d = df.copy() if cols is None else df[cols].copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else (f"{x:.3g}" if "p_" in c or c.startswith("p") else f"{x:.{digits}f}"))
    head = "| " + " | ".join(d.columns) + " |"
    sep = "|" + "---|" * len(d.columns)
    body = ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results_cluster"))
    ap.add_argument("--release", default=str(PROJECT_ROOT / "release"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "revision"))
    ap.add_argument("--seed", type=int, default=2027)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    df = load(Path(a.results))

    ss, cells = sample_sizes(df)
    ss.to_csv(out / "A_sample_sizes_runs.csv", index=False)
    cells.to_csv(out / "A_sample_sizes_cells.csv", index=False)
    e1, e1d = exp1(df, rng)
    e1.to_csv(out / "B_exp1_rates.csv", index=False)
    e1d.to_csv(out / "B_exp1_strong_minus_none.csv", index=False)
    e2 = exp2(df, rng)
    e2.to_csv(out / "C_exp2_rates.csv", index=False)
    br = breaking(e2)
    br.to_csv(out / "C_exp2_breaking.csv", index=False)
    sf = same_filler(df, rng)
    sf.to_csv(out / "D_same_filler.csv", index=False)
    fig_same_filler(sf, out)
    e3 = exp3(df, rng)
    e3.to_csv(out / "E_exp3_copies.csv", index=False)
    e4 = exp4(df, rng)
    e4.to_csv(out / "F_exp4_wikipedia.csv", index=False)
    pr = paired(df, rng)
    pr.to_csv(out / "G_paired.csv", index=False)
    sd = sdt(df, rng)
    sd.to_csv(out / "H_decision_sdt.csv", index=False)
    tw = three_way(df)
    tw.to_csv(out / "I_three_way.csv", index=False)
    n_aud = audit_nullscale(df, out, rng)
    n_wiki = audit_wikipedia(Path(a.release), df, out, rng)

    main_runs = ss[ss["model"].isin(MODELS)]
    R = ["# Revision checks", "",
         f"Scored answers in the paper (seven models, bf16 audit excluded): {main_runs['answers'].sum():,}. "
         f"With the bf16 audit: {ss['answers'].sum():,}.", "",
         "All intervals are 95% percentile intervals from 2,000 bootstrap resamples of whole documents within a cell. "
         "Unpaired differences use independent document resamples and a document-level permutation test. "
         "Paired differences (same questions) resample documents jointly and use an exact McNemar test.", "",
         "## A. Cell sizes (unanswerable questions and documents per cell, main runs)", "",
         fmt(cells.groupby(["experiment", "cell"]).agg(unanswerable_min=("unanswerable", "min"), unanswerable_max=("unanswerable", "max"),
                                                      documents_min=("documents", "min"), documents_max=("documents", "max")).reset_index()), "",
         "## B. Exp 1, strong minus none (points)", "",
         fmt(e1d), "",
         "## C. Exp 2 breaking length, Wilson vs document bootstrap", "",
         fmt(br), "",
         "## D. Same filler comparison inside Exp 2 (points)", "",
         fmt(sf[["model", "filler", "longest", "strong_32k", "none_longest", "gap_strong32_vs_none_longest",
                 "gap_strong32_vs_none_longest_lo", "gap_strong32_vs_none_longest_hi", "lookalike_effect_8k",
                 "lookalike_effect_longest", "length_effect_none", "length_effect_none_lo", "length_effect_none_hi"]]), "",
         "## E. Exp 3 copies, 8 minus 1 copy", "",
         fmt(e3[["model", "c1", "c2", "c4", "c8", "diff_8_minus_1", "diff_lo", "diff_hi", "p_doc_perm", "p_holm"]]), "",
         "## F. Exp 4 Wikipedia", "",
         fmt(e4[["model", "passages", "length", "k", "n", "rate", "boot_lo", "boot_hi"]]), "",
         "## G. Paired comparisons", "",
         fmt(pr), "",
         "## H. Answer or refuse decision (corrected signal detection)", "",
         "Hit rate = share of answerable questions the model answers at all (correct or wrong value). "
         "False alarm rate = share of unanswerable strong look-alike questions it answers. "
         "Both from the same documents, unscorable answers removed. Correctness is reported separately.", "",
         fmt(sd, digits=2), "",
         "## I. Automatic three-way split (strong look-alike, Exp 1)", "",
         fmt(tw), "",
         "## J. Audit sheets", "",
         f"- audit_nullscale_sheet.csv: {n_aud} Exp 1 strong look-alike answers (12 made up and 3 refusals per model and ladder), shuffled, model hidden. Key in audit_nullscale_key.csv.",
         f"- audit_wikipedia_sheet.csv: {n_wiki} Exp 4 made up answers with similar passages (up to 15 per model). Key in audit_wikipedia_key.csv.",
         "",
         "Labels for audit_nullscale_sheet.csv, column label:",
         "- R: refuses, states no value for the asked record",
         "- W: states the look-alike's value but explicitly says it belongs to a different name, building or year",
         "- U: states a value as the answer without any warning (unsupported answer)",
         "- O: other or unclear",
         "",
         "Labels for audit_wikipedia_sheet.csv, column answer_in_passages:",
         "- yes: the passages state the answer, also in other words, so the question was not truly unanswerable",
         "- no: the passages do not state it",
         "- unsure",
         "Run python -m analysis.wiki_context_check --data <folder with exp6/docs> first; it marks items whose true answer string appears in the passages.",
         ""]
    (out / "report.md").write_text("\n".join(R), encoding="utf-8")
    print("\n".join(R))


if __name__ == "__main__":
    main()
