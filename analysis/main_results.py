"""analysis/main_results.py

Main results for the paper from the official scores of every model: Exp 2 (look-alike ladder),
Exp 3 (length with and without a strong look-alike), Exp 4 (copies), sibling filler, temperature
stability, and a logistic regression that gives the exchange rate (doublings of length that equal one
strong look-alike).

Step 9 additions (6 October 2026, after seeing the data; listed in the hypotheses.md change log)
  * the full-data regression is the MAIN result, with a 95% document-bootstrap interval for the exchange rate;
    the version without Llama 3.3 70B at 128K is shown only as a labeled SENSITIVITY CHECK
  * breaking length: the first length whose no-look-alike made-up rate is clearly above 8K (Wilson intervals
    do not overlap), with answer accuracy at the same length
  * prediction 4: answer accuracy, wrong refusals and wrong values for sibling vs unrelated filler
  * strict-prompt runs (exp2_<model>_strict_t0_s0) are kept out of every table above and get their own table
  * main_results.json: the headline numbers, read by analysis/results_summary.py

Input   the per-run folders written by score/score_all.py, each with a scored.csv:
            <results>/<exp>_<model>_normal_t<T>_s<seed>/scored.csv
        (on the cluster: outputs/results; on the PC after copying: outputs/results_cluster)
Output  outputs/figures_main/   fig8_exp2_ladder, fig9_exp3_length, fig10_exp4_copies, fig11_filler
                                (900 dpi .png + .pdf), main_results.md (all numbers), main_results.csv

Usage (any machine, no GPU; seconds)
  python -m analysis.main_results --results outputs/results_cluster
  python -m analysis.main_results --results outputs/results_cluster --boot 200    # faster bootstrap
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

MODELS = ["qwen3_4b", "llama31_8b", "gemma3_27b", "qwen3_30b_a3b", "llama33_70b", "qwen3_next_80b", "glm45_air"]
NAMES = {"qwen3_4b": "Qwen3 4B", "llama31_8b": "Llama 3.1 8B", "gemma3_27b": "Gemma 3 27B",
         "qwen3_30b_a3b": "Qwen3 30B-A3B", "llama33_70b": "Llama 3.3 70B", "qwen3_next_80b": "Qwen3-Next 80B",
         "glm45_air": "GLM-4.5-Air"}
# reference categorical palette, slots 1-7 in fixed order (validated: scripts/validate_palette.js, light mode)
COLORS = dict(zip(MODELS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]))
MARKERS = dict(zip(MODELS, ["o", "s", "^", "D", "v", "P", "X"]))
LEVELS = ["none", "weak", "medium", "strong"]
LENGTHS = [8, 32, 64, 128]
COPIES = [1, 2, 4, 8]


# ----------------------------------------------------------------------------- data

def load(results: Path) -> list[dict]:
    rows = []
    for f in sorted(results.glob("*/scored.csv")):
        name = f.parent.name
        exp = name.split("_")[0]
        rest = name[len(exp) + 1:]
        prompt = next((pr for pr in ("normal", "strict", "batch12") if f"_{pr}_" in rest), None)
        if prompt is None:
            continue
        model, run = rest.split(f"_{prompt}_")
        if model not in MODELS:
            continue
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                r.update(exp=exp, model=model, run=run, prompt=prompt, answerable=r["answerable"] == "True",
                         made_up=r["label"] == "made_up", captured=r.get("captured") == "True",
                         length=int(r["length_k"]), copies_n=int(r["copies"] or 0), doc=r["qid"].split("/")[0])
                rows.append(r)
    return rows


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, c - h), min(1.0, c + h)


def rate(rs):
    rs = [r for r in rs if not r["answerable"]]
    return wilson(sum(r["made_up"] for r in rs), len(rs)) + (len(rs),)


def pct(rs):
    p, lo, hi, n = rate(rs)
    return "-" if n == 0 else f"{100 * p:.1f} [{100 * lo:.0f}-{100 * hi:.0f}]"


# ----------------------------------------------------------------------------- logistic regression (IRLS)

def logit(X, y, w=None, iters=50):
    """Weighted logistic regression by IRLS. Returns (coef, standard errors)."""
    import numpy as np
    X, y = np.asarray(X, float), np.asarray(y, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    b = np.zeros(X.shape[1])
    ridge = 1e-6 * np.eye(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = w * p * (1 - p)
        H = X.T @ (X * W[:, None]) + ridge
        g = X.T @ (w * (y - p))
        step = np.linalg.solve(H, g)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    eta = np.clip(X @ b, -30, 30)
    p = 1 / (1 + np.exp(-eta))
    H = X.T @ (X * (w * p * (1 - p))[:, None]) + ridge
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return b, se


def exchange_rate(rows, models, exclude=lambda r: False):
    """Exp 3, questions with no answer: made_up ~ log2(length/8) + strong + model + ladder.
    Exchange rate = coef(strong) / coef(log2 length): doublings of length worth one strong look-alike."""
    import numpy as np
    rs = [r for r in rows if r["exp"] == "exp3" and not r["answerable"] and r["model"] in models and not exclude(r)]
    if not rs:
        return None
    ms = [m for m in models if any(r["model"] == m for r in rs)]
    X, y = [], []
    for r in rs:
        x = [1.0, math.log2(r["length"] / 8), 1.0 if r["level"] == "strong" else 0.0,
             1.0 if r["ladder"] == "role" else 0.0, 1.0 if r["filler"] == "sibling" else 0.0]
        x += [1.0 if r["model"] == m else 0.0 for m in ms[1:]]
        X.append(x)
        y.append(1.0 if r["made_up"] else 0.0)
    b, se = logit(X, y)
    out = {"n": len(y), "b_len": b[1], "se_len": se[1], "b_strong": b[2], "se_strong": se[2],
           "b_role": b[3], "b_sibling": b[4], "se_sibling": se[4]}
    # interaction model: length can matter differently with and without a look-alike
    Xi = [x[:5] + [x[1] * x[2]] + x[5:] for x in X]
    bi, sei = logit(Xi, y)
    out.update(b_len_none=bi[1], se_len_none=sei[1], b_strong_8k=bi[2], se_strong_8k=sei[2],
               b_len_strong=bi[1] + bi[5], b_inter=bi[5], se_inter=sei[5])
    # exchange rate: how many doublings of length (with no look-alike) add as much log-odds as one strong
    # look-alike adds at 8K. Defined only when length has a clearly positive effect (lower 95% bound > 0).
    out["exchange"] = (bi[2] / bi[1]) if bi[1] - 1.96 * sei[1] > 0 else float("nan")
    return out


def exchange_boot(rows, models, B=500, seed=0, exclude=lambda r: False):
    """95% interval for the exchange rate: documents resampled within each model, B times."""
    import numpy as np
    rs = [r for r in rows if r["exp"] == "exp3" and not r["answerable"] and r["model"] in models and not exclude(r)]
    if not rs or B <= 0:
        return float("nan"), float("nan")
    ms = [m for m in models if any(r["model"] == m for r in rs)]
    X, y, keys = [], [], []
    for r in rs:
        x = [1.0, math.log2(r["length"] / 8), 1.0 if r["level"] == "strong" else 0.0,
             1.0 if r["ladder"] == "role" else 0.0, 1.0 if r["filler"] == "sibling" else 0.0]
        X.append(x + [x[1] * x[2]] + [1.0 if r["model"] == m else 0.0 for m in ms[1:]])
        y.append(1.0 if r["made_up"] else 0.0)
        keys.append((r["model"], r["doc"]))
    X, y = np.asarray(X), np.asarray(y)
    uniq = sorted(set(keys))
    pos = {k: i for i, k in enumerate(uniq)}
    gi = np.array([pos[k] for k in keys])
    by_model = defaultdict(list)
    for k in uniq:
        by_model[k[0]].append(pos[k])
    rng = np.random.default_rng(seed)
    est = []
    for _ in range(B):
        counts = np.zeros(len(uniq))
        for ids in by_model.values():
            np.add.at(counts, rng.choice(ids, size=len(ids), replace=True), 1)
        b, _ = logit(X, y, counts[gi])
        if b[1] > 0:
            est.append(b[2] / b[1])
    if len(est) < 0.9 * B:
        return float("nan"), float("nan")
    return float(np.quantile(est, 0.025)), float(np.quantile(est, 0.975))


def accuracy(rs):
    """(rate, lo, hi, n) over questions WITH an answer."""
    rs = [r for r in rs if r["answerable"]]
    return wilson(sum(r["label"] == "correct" for r in rs), len(rs)) + (len(rs),)



def _pct1(x):
    return "%.1f" % (100 * x)


def _brk_rate(v):
    return "%.1f [%.0f-%.0f]" % (100 * v[0], 100 * v[1], 100 * v[2])

def breaking_lengths(rows, models):
    """Exp 3, no look-alike, fillers pooled. Break = first length > 8K whose Wilson interval lies fully above
    the 8K interval. Accuracy drop = first length whose accuracy interval lies fully below 8K's (>= 10 points)."""
    out = []
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m]
        none = {L: rate([r for r in e3 if r["level"] == "none" and r["length"] == L]) for L in LENGTHS}
        acc = {L: accuracy([r for r in e3 if r["length"] == L]) for L in LENGTHS}
        docs = {L: len({r["doc"] for r in e3 if r["length"] == L}) for L in LENGTHS}
        brk = next((L for L in LENGTHS[1:] if none[L][3] and none[L][1] > none[8][2]), None)
        drop = next((L for L in LENGTHS[1:] if acc[L][3] and acc[L][2] < acc[8][1] and acc[8][0] - acc[L][0] >= 0.10), None)
        out.append({"model": m, "none": none, "acc": acc, "docs": docs, "break": brk, "drop": drop})
    return out


# ----------------------------------------------------------------------------- figures

def _style():
    import matplotlib
    matplotlib.use("Agg")
    import make_figures  # noqa: F401  (sets rcParams)
    from make_figures import FULL_W, GRID, INK2, SURFACE, save
    return FULL_W, GRID, INK2, SURFACE, save


def _line(ax, xs, rs_by_x, m, SURFACE, off=0.0):
    pts = [(x, rate(rs_by_x[x])) for x in xs]
    pts = [(x, v) for x, v in pts if v[3] > 0]
    if not pts:
        return
    xi = [xs.index(x) + off for x, _ in pts]
    ys = [100 * v[0] for _, v in pts]
    lo = [100 * (v[0] - v[1]) for _, v in pts]
    hi = [100 * (v[2] - v[0]) for _, v in pts]
    ax.errorbar(xi, ys, yerr=[lo, hi], color=COLORS[m], marker=MARKERS[m], ms=4.5, lw=1.6, capsize=1.8,
                elinewidth=0.8, mec=SURFACE, mew=0.8, label=NAMES[m], zorder=3)


def fig_exp2(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.6), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, lad in zip(axes, ["name", "role"]):
        for i, m in enumerate(models):
            by = {lv: [r for r in rows if r["exp"] == "exp2" and r["run"] == "t0_s0" and r["model"] == m
                       and r["ladder"] == lad and r["level"] == lv] for lv in LEVELS}
            _line(ax, LEVELS, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
        ax.set_xticks(range(4), LEVELS)
        ax.set_xlabel("look-alike level (length fixed at 32K)")
        ax.set_title(f"({'a' if lad == 'name' else 'b'}) {lad} ladder", loc="left")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("made-up answers (%)")
    axes[1].legend(loc="upper left", fontsize=6.4, handlelength=1.6, ncol=1)
    fig.text(0.01, 1.0, "Exp 2: questions with no answer; 120 documents (960 no-answer questions) per model; "
             "bars: 95% Wilson interval; T = 0", fontsize=6.4, color=INK2)
    save(fig, out, "fig8_exp2_ladder", dpi)


def fig_exp3(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.6), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, lv, title in zip(axes, ["none", "strong"], ["(a) no look-alike", "(b) one strong look-alike"]):
        for i, m in enumerate(models):
            by = {L: [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == lv
                      and r["length"] == L] for L in LENGTHS}
            _line(ax, LENGTHS, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
        ax.set_xticks(range(4), [f"{L}K" for L in LENGTHS])
        ax.set_xlabel("document length (tokens)")
        ax.set_title(title, loc="left")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("made-up answers (%)")
    axes[1].legend(loc="lower left", fontsize=6.2, handlelength=1.6, ncol=2)
    if "llama33_70b" in models:
        axes[0].annotate("Llama 3.3 70B at 128K:\nanswer accuracy also\ncollapses (see text)",
                         xy=(2.95, 74), xytext=(0.9, 60), fontsize=6, color=INK2,
                         arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.6})
    fig.text(0.01, 1.0, "Exp 3: fillers pooled; 640 no-answer questions per point; Gemma 3 27B not run at 128K; "
             "GLM-4.5-Air: half of the 128K documents fit its window", fontsize=6.4, color=INK2)
    save(fig, out, "fig9_exp3_length", dpi)


def fig_exp4(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    fig, ax = plt.subplots(figsize=(FULL_W * 0.55, 2.5))
    for i, m in enumerate(models):
        by = {c: [r for r in rows if r["exp"] == "exp4" and r["model"] == m and r["copies_n"] == c] for c in COPIES}
        _line(ax, COPIES, by, m, SURFACE, off=(i - (len(models) - 1) / 2) * 0.04)
    ax.set_xticks(range(4), [str(c) for c in COPIES])
    ax.set_xlabel("copies of the strong look-alike (32K)")
    ax.set_ylabel("made-up answers (%)")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=6, handlelength=1.4, ncol=2)
    ax.set_title("Exp 4: more copies of the same look-alike", loc="left")
    save(fig, out, "fig10_exp4_copies", dpi)


def fig_filler(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    from make_figures import BLUE, ORANGE
    fig, ax = plt.subplots(figsize=(FULL_W * 0.6, 2.4))
    x = list(range(len(models)))
    for off, fil, col, lab in ((-0.19, "unrelated", ORANGE, "unrelated filler"), (0.19, "sibling", BLUE, "sibling filler")):
        vals, lo, hi = [], [], []
        for m in models:
            p, l_, h_, n = rate([r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == "strong"
                                 and r["filler"] == fil])
            vals.append(100 * p), lo.append(100 * (p - l_)), hi.append(100 * (h_ - p))
        ax.bar([i + off for i in x], vals, width=0.36, color=col, edgecolor=SURFACE, linewidth=1, label=lab, zorder=2)
        ax.errorbar([i + off for i in x], vals, yerr=[lo, hi], fmt="none", ecolor=INK2, elinewidth=0.7, capsize=1.5, zorder=3)
    ax.set_xticks(x, [NAMES[m].replace(" ", "\n", 1) for m in models], fontsize=6.4)
    ax.set_ylabel("made-up answers (%)")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.4, ncol=2)
    ax.set_title("Strong look-alike: filler type (Exp 3, all lengths)", loc="left", pad=16)
    save(fig, out, "fig11_filler", dpi)


# ----------------------------------------------------------------------------- report

def fig_exp6(rows, models, out, dpi):
    import matplotlib.pyplot as plt
    FULL_W, GRID, INK2, SURFACE, save = _style()
    from make_figures import BLUE, ORANGE
    ms = [m for m in models if any(r["exp"] == "exp6" and r["model"] == m for r in rows)]
    if not ms:
        return
    fig, axes = plt.subplots(1, 2, figsize=(FULL_W, 2.5), sharey=True, gridspec_kw={"wspace": 0.06})
    x = list(range(len(ms)))
    for ax, Lk in zip(axes, (8, 32)):
        for off, lv, col, lab in ((-0.19, "lookalike", ORANGE, "look-alike passages"), (0.19, "random", BLUE, "random passages")):
            vals, lo, hi = [], [], []
            for m in ms:
                p, l_, h_, n = rate([r for r in rows if r["exp"] == "exp6" and r["model"] == m and r["level"] == lv
                                     and r["length"] == Lk])
                vals.append(100 * p if n else 0), lo.append(100 * (p - l_) if n else 0), hi.append(100 * (h_ - p) if n else 0)
            ax.bar([i + off for i in x], vals, width=0.36, color=col, edgecolor=SURFACE, linewidth=1, label=lab, zorder=2)
            ax.errorbar([i + off for i in x], vals, yerr=[lo, hi], fmt="none", ecolor=INK2, elinewidth=0.7, capsize=1.5, zorder=3)
        ax.set_xticks(x, [NAMES[m].replace(" ", "\n", 1) for m in ms], fontsize=6)
        ax.set_title(f"({'a' if Lk == 8 else 'b'}) {Lk}K, answer passage removed", loc="left")
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("made-up answers (%)")
    axes[0].legend(loc="upper left", fontsize=6.4)
    fig.text(0.01, 1.0, "Exp 6: 300 Natural Questions per bar; bars: 95% Wilson interval", fontsize=6.4, color=INK2)
    save(fig, out, "fig12_exp6_wikipedia", dpi)


def report(rows, models, out, strict=(), boot=500):
    L = ["# Main results (official scoring)", "",
         f"Models with results: {', '.join(NAMES[m] for m in models)}.", "",
         "Made-up rate = share of questions with no answer where the model gave a value; 95% Wilson interval in brackets.", "",
         "## Exp 2: look-alike ladder at 32K (T = 0)", "",
         "| model | none | weak | medium | strong | copied look-alike | correct (with answer) |", "|---|---|---|---|---|---|---|"]
    table = []
    for m in models:
        e2 = [r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == "t0_s0"]
        mu = [r for r in e2 if r["made_up"]]
        an = [r for r in e2 if r["answerable"]]
        cells = [pct([r for r in e2 if r["level"] == lv]) for lv in LEVELS]
        cap = f"{100 * sum(r['captured'] for r in mu) / len(mu):.0f}%" if mu else "-"
        acc = f"{100 * sum(r['label'] == 'correct' for r in an) / len(an):.1f}%" if an else "-"
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + f" | {cap} | {acc} |")
        for lv in LEVELS:
            p, lo, hi, n = rate([r for r in e2 if r["level"] == lv])
            table.append({"exp": "exp2", "model": m, "condition": lv, "made_up": round(p, 4), "lo": round(lo, 4),
                          "hi": round(hi, 4), "n": n})
    L += ["", "## Exp 2 stability: strong look-alike at T = 0.7, three seeds", "",
          "| model | T=0 | seed 1 | seed 2 | seed 3 |", "|---|---|---|---|---|"]
    for m in models:
        cells = [pct([r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == run and r["level"] == "strong"])
                 for run in ("t0_s0", "t0.7_s1", "t0.7_s2", "t0.7_s3")]
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    L += ["", "## Exp 3: length, with and without a strong look-alike (fillers pooled)", "",
          "| model | " + " | ".join(f"none {x}K" for x in LENGTHS) + " | " + " | ".join(f"strong {x}K" for x in LENGTHS) + " |",
          "|---|" + "---|" * 8]
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m]
        cells = [pct([r for r in e3 if r["level"] == lv and r["length"] == Lk]) for lv in ("none", "strong") for Lk in LENGTHS]
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
        for lv in ("none", "strong"):
            for Lk in LENGTHS:
                p, lo, hi, n = rate([r for r in e3 if r["level"] == lv and r["length"] == Lk])
                if n:
                    table.append({"exp": "exp3", "model": m, "condition": f"{lv}_{Lk}k", "made_up": round(p, 4),
                                  "lo": round(lo, 4), "hi": round(hi, 4), "n": n})
    L += ["", "Answer accuracy on questions WITH an answer, Exp 3 (checks that a model can still read at that length):", "",
          "| model | " + " | ".join(f"{x}K" for x in LENGTHS) + " |", "|---|" + "---|" * 4]
    for m in models:
        cells = []
        for Lk in LENGTHS:
            an = [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["length"] == Lk and r["answerable"]]
            cells.append(f"{100 * sum(r['label'] == 'correct' for r in an) / len(an):.1f}%" if an else "-")
        L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")
    L += ["", "## Exp 3: filler type with a strong look-alike (all lengths)", "",
          "| model | unrelated filler | sibling filler |", "|---|---|---|"]
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m and r["level"] == "strong"]
        L.append(f"| {NAMES[m]} | {pct([r for r in e3 if r['filler'] == 'unrelated'])} | {pct([r for r in e3 if r['filler'] == 'sibling'])} |")
    L += ["", "## Exp 4: copies of the same strong look-alike (32K)", "",
          "| model | " + " | ".join(f"{c} cop{'y' if c == 1 else 'ies'}" for c in COPIES) + " |", "|---|" + "---|" * 4]
    for m in models:
        e4 = [r for r in rows if r["exp"] == "exp4" and r["model"] == m]
        L.append(f"| {NAMES[m]} | " + " | ".join(pct([r for r in e4 if r["copies_n"] == c]) for c in COPIES) + " |")

    # ---------------- Exp 6
    e6m = [m for m in models if any(r["exp"] == "exp6" and r["model"] == m for r in rows)]
    if e6m:
        sets = [("lookalike", 8), ("random", 8), ("lookalike", 32), ("random", 32)]
        L += ["", "## Exp 6: real Wikipedia text (Natural Questions, gold passage removed)", "",
              "Made-up rate on questions whose answer was removed; 300 questions per cell. 'From memory' = made-up answers "
              "that are in fact the true answer (the model knew it without the document).", "",
              "| model | look-alike 8K | random 8K | look-alike 32K | random 32K | from memory | control: correct with gold passage (8K) |",
              "|---|---|---|---|---|---|---|"]
        for m in e6m:
            e6 = [r for r in rows if r["exp"] == "exp6" and r["model"] == m]
            cells = [pct([r for r in e6 if r["level"] == lv and r["length"] == Lk]) for lv, Lk in sets]
            mu = [r for r in e6 if r["made_up"]]
            mem = f"{100 * sum(r.get('source') == 'true_answer_from_memory' for r in mu) / len(mu):.0f}%" if mu else "-"
            g = [r for r in e6 if r["level"] == "gold"]
            acc = f"{100 * sum(r['label'] == 'correct' for r in g) / len(g):.1f}%" if g else "-"
            L.append(f"| {NAMES[m]} | " + " | ".join(cells) + f" | {mem} | {acc} |")
            for lv, Lk in sets:
                p, lo, hi, n = rate([r for r in e6 if r["level"] == lv and r["length"] == Lk])
                if n:
                    table.append({"exp": "exp6", "model": m, "condition": f"{lv}_{Lk}k", "made_up": round(p, 4),
                                  "lo": round(lo, 4), "hi": round(hi, 4), "n": n})
    # ---------------- Exp 7
    e7m = [m for m in models if any(r["exp"] == "exp7" and r["model"] == m for r in rows)]
    if e7m:
        L += ["", "## Exp 7: one question per call vs 12 questions in one call (32K, strong look-alike)", "",
              "| model | made up: one per call | made up: 12 in one call | correct (with answer): one per call | correct: 12 in one call |",
              "|---|---|---|---|---|"]
        for m in e7m:
            cells = []
            for pr in ("normal", "batch12"):
                cells.append(pct([r for r in rows if r["exp"] == "exp7" and r["model"] == m and r["prompt"] == pr]))
            for pr in ("normal", "batch12"):
                an = [r for r in rows if r["exp"] == "exp7" and r["model"] == m and r["prompt"] == pr and r["answerable"]]
                cells.append(f"{100 * sum(r['label'] == 'correct' for r in an) / len(an):.1f}%" if an else "-")
            L.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")

    # ---------------- Step 9: breaking length
    BL = breaking_lengths(rows, models)
    L += ["", "## Exp 3: breaking length (no look-alike, fillers pooled)", "",
          "Break = first length whose 95% interval lies fully above the 8K interval. Accuracy drop = first length whose "
          "accuracy interval lies fully below the 8K interval and is at least 10 points lower. Documents = documents run "
          "at that length (fewer than 80 = only part fit the model's window). Defined on 6 Oct 2026, after seeing the data.", "",
          "| model | made up, no look-alike: 8K / 32K / 64K / 128K | answer accuracy: 8K / 32K / 64K / 128K | documents | "
          "breaking length | made up there | accuracy there | accuracy drop starts |", "|---|---|---|---|---|---|---|---|"]
    for b in BL:
        f1 = lambda v: "-" if v[3] == 0 else f"{100 * v[0]:.1f}"
        brk = b["break"]
        L.append(f"| {NAMES[b['model']]} | " + " / ".join(f1(b["none"][x]) for x in LENGTHS) + " | "
                 + " / ".join(f1(b["acc"][x]) for x in LENGTHS) + " | " + " / ".join(str(b["docs"][x]) for x in LENGTHS)
                 + " | " + (f"{brk}K" if brk else "none up to 128K")
                 + " | " + (_brk_rate(b["none"][brk]) if brk else "-")
                 + " | " + (_pct1(b["acc"][brk][0]) + "%" if brk else "-")
                 + " | " + (str(b["drop"]) + "K" if b["drop"] else "none") + " |")
    # ---------------- Step 9: prediction 4, filler type and answer accuracy
    L += ["", "## Exp 3: filler type and answer accuracy (pre-registered prediction 4)", "",
          "Questions WITH an answer, all lengths: accuracy, wrong refusals (said not found) and wrong values, in %.", "",
          "| model | made up (strong): unrelated | sibling | accuracy: unrelated | sibling | change (points) | "
          "wrong refusals: unrelated / sibling | wrong values: unrelated / sibling |", "|---|---|---|---|---|---|---|---|"]
    acc_changes, fill_lower = [], 0
    for m in models:
        e3 = [r for r in rows if r["exp"] == "exp3" and r["model"] == m]
        u_rows = [r for r in e3 if r["level"] == "strong" and r["filler"] == "unrelated"]
        sb_rows = [r for r in e3 if r["level"] == "strong" and r["filler"] == "sibling"]
        u, sb = rate(u_rows), rate(sb_rows)
        au, asb = (accuracy([r for r in e3 if r["filler"] == f]) for f in ("unrelated", "sibling"))
        share = lambda f, lab: 100 * sum(r["label"] == lab for r in e3 if r["answerable"] and r["filler"] == f) / max(
            1, sum(r["answerable"] and r["filler"] == f for r in e3))
        acc_changes.append(asb[0] - au[0])
        fill_lower += sb[0] < u[0]
        L.append(f"| {NAMES[m]} | {pct(u_rows)} | {pct(sb_rows)} | {100 * au[0]:.1f} | {100 * asb[0]:.1f} | {100 * (asb[0] - au[0]):+.1f} | "
                 f"{share('unrelated', 'wrong_refusal'):.1f} / {share('sibling', 'wrong_refusal'):.1f} | "
                 f"{share('unrelated', 'wrong'):.1f} / {share('sibling', 'wrong'):.1f} |")
    p4 = ("partly supported" if fill_lower == len(models) else "not supported")
    L += ["", f"**Prediction 4: {p4}.** Sibling filler lowers made-up answers in {fill_lower} of {len(models)} models, but "
          f"answer accuracy changes by {100 * min(acc_changes):+.1f} to {100 * max(acc_changes):+.1f} points"
          + (" (accuracy does NOT hold)." if min(acc_changes) < -0.02 else " (accuracy holds).")]
    # ---------------- strict prompt (only if run)
    if strict:
        sm = [m for m in models if any(r["model"] == m for r in strict)]
        L += ["", "## Exp 2, strong look-alike: normal prompt vs strict prompt (32K)", "",
              "| model | made up: normal | strict | accuracy: normal | strict |", "|---|---|---|---|---|"]
        for m in sm:
            nr = [r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == "t0_s0" and r["level"] == "strong"]
            sr = [r for r in strict if r["model"] == m and r["level"] == "strong"]
            L.append(f"| {NAMES[m]} | {pct(nr)} | {pct(sr)} | {100 * accuracy(nr)[0]:.1f} | "
                     f"{100 * accuracy(sr)[0]:.1f} |" if accuracy(sr)[3] else
                     f"| {NAMES[m]} | {pct(nr)} | {pct(sr)} | {100 * accuracy(nr)[0]:.1f} | - |")
    # ---------------- Step 9: regression, main result + sensitivity check
    summary = {"models": [NAMES[m] for m in models]}
    try:
        reg = exchange_rate(rows, models)
        excl = lambda r: r["model"] == "llama33_70b" and r["length"] == 128
        reg_x = exchange_rate(rows, models, exclude=excl)
        ci = exchange_boot(rows, models, boot)
        ci_x = exchange_boot(rows, models, boot, exclude=excl)
    except Exception as e:                  # numpy missing
        reg = reg_x = None
        L += ["", f"(regression skipped: {e})"]
    for title, rg, cc in (("MAIN RESULT: all Exp 3 answers", reg, ci if reg else None),
                          ("SENSITIVITY CHECK (added after seeing the data, not the main result): without Llama 3.3 70B "
                           "at 128K, where its reading collapses", reg_x, ci_x if reg_x else None)):
        if not rg:
            continue
        L += ["", f"## Logistic regression, Exp 3, {title} ({rg['n']:,} no-answer questions)", "",
              "made_up ~ log2(length / 8K) + strong look-alike + ladder + filler + model", "",
              "| term | log-odds | SE | odds ratio |", "|---|---|---|---|",
              f"| one doubling of length | {rg['b_len']:.3f} | {rg['se_len']:.3f} | {math.exp(rg['b_len']):.2f} |",
              f"| strong look-alike | {rg['b_strong']:.3f} | {rg['se_strong']:.3f} | {math.exp(rg['b_strong']):.1f} |",
              f"| sibling filler | {rg['b_sibling']:.3f} | {rg['se_sibling']:.3f} | {math.exp(rg['b_sibling']):.2f} |", "",
              (f"**Exchange rate:** one strong look-alike adds as much as **{rg['exchange']:.1f} doublings of length** "
               f"(95% document-bootstrap interval {cc[0]:.1f} to {cc[1]:.1f}, {boot} draws); i.e. a document "
               f"{2 ** rg['exchange']:,.0f}x longer (log-odds {rg['b_strong_8k']:.2f} for the look-alike at 8K / "
               f"{rg['b_len_none']:.2f} per doubling without a look-alike)." if math.isfinite(rg["exchange"]) else
               "**Exchange rate:** not defined, because length has no clearly positive effect."),
              f"With an interaction term: one doubling raises the log-odds by {rg['b_len_none']:.3f} (SE {rg['se_len_none']:.3f}) "
              f"without a look-alike and by {rg['b_len_strong']:.3f} with a strong one."]
    if reg:
        summary.update(exchange=reg["exchange"], exchange_lo=ci[0], exchange_hi=ci[1],
                       exchange_sens=reg_x["exchange"] if reg_x else None, or_strong=math.exp(reg["b_strong"]),
                       or_doubling=math.exp(reg["b_len"]), or_sibling=math.exp(reg["b_sibling"]), n_reg=reg["n"],
                       b_len_none=reg["b_len_none"], b_len_strong=reg["b_len_strong"])
    gaps = []
    for m in models:
        e2 = [r for r in rows if r["exp"] == "exp2" and r["model"] == m and r["run"] == "t0_s0"]
        sv, nv = rate([r for r in e2 if r["level"] == "strong"]), rate([r for r in e2 if r["level"] == "none"])
        mu = [r for r in e2 if r["made_up"]]
        gaps.append({"model": NAMES[m], "none": nv[0], "strong": sv[0], "separate": sv[1] > nv[2],
                     "captured": sum(r["captured"] for r in mu) / len(mu) if mu else None})
    summary.update(exp2=gaps, breaking=[{"model": NAMES[b["model"]], "break_k": b["break"], "drop_k": b["drop"],
                                         "made_up_at_break": b["none"][b["break"]][0] if b["break"] else None,
                                         "acc_8k": b["acc"][8][0], "acc_at_break": b["acc"][b["break"]][0] if b["break"] else None,
                                         "made_up_128k": b["none"][128][0] if b["none"][128][3] else None,
                                         "made_up_max": max(b["none"][x][0] for x in LENGTHS if b["none"][x][3]),
                                         "max_at_k": max((x for x in LENGTHS if b["none"][x][3]), key=lambda x: b["none"][x][0]),
                                         "acc_at_max": b["acc"][max((x for x in LENGTHS if b["none"][x][3]),
                                                                    key=lambda x: b["none"][x][0])][0]}
                                        for b in BL],
                   filler_lower_in=fill_lower, filler_acc_change_min=min(acc_changes), filler_acc_change_max=max(acc_changes),
                   p4=p4)
    e7 = {}
    for m in models:
        one = [r for r in rows if r["exp"] == "exp7" and r["model"] == m and r["prompt"] == "normal"]
        b12 = [r for r in rows if r["exp"] == "exp7" and r["model"] == m and r["prompt"] == "batch12"]
        if one and b12:
            e7[NAMES[m]] = {"one": rate(one)[0], "twelve": rate(b12)[0]}
    e6 = {}
    for m in models:
        e6r = [r for r in rows if r["exp"] == "exp6" and r["model"] == m]
        if e6r:
            e6[NAMES[m]] = {"lookalike_32k": rate([r for r in e6r if r["level"] == "lookalike" and r["length"] == 32])[0],
                            "random_32k": rate([r for r in e6r if r["level"] == "random" and r["length"] == 32])[0]}
    summary.update(exp7=e7, exp6=e6, exp6_missing=[NAMES[m] for m in models if NAMES[m] not in e6])
    (out / "main_results.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (out / "main_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(out / "main_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    print("\n".join(L))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(PROJECT_ROOT / "outputs" / "results"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "figures_main"))
    ap.add_argument("--dpi", type=int, default=900)
    ap.add_argument("--boot", type=int, default=500, help="bootstrap draws for the exchange-rate interval (0 = skip)")
    a = ap.parse_args(argv)
    rows = load(Path(a.results))
    if not rows:
        sys.exit(f"no scored.csv files under {a.results}")
    models = [m for m in MODELS if any(r["model"] == m for r in rows)]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    strict = [r for r in rows if r["prompt"] == "strict"]
    rows = [r for r in rows if r["prompt"] != "strict"]      # strict runs never mix into the main tables
    print(f"{len(rows):,} scored answers from {len(models)} models ({len(strict):,} strict-prompt answers kept apart)\n")
    report(rows, models, out, strict, a.boot)
    fig_exp2(rows, models, out, a.dpi)
    fig_exp3(rows, models, out, a.dpi)
    fig_exp4(rows, models, out, a.dpi)
    fig_filler(rows, models, out, a.dpi)
    fig_exp6(rows, models, out, a.dpi)
    print(f"\nsaved to {out}")


if __name__ == "__main__":
    main()
